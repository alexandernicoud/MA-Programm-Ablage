import os
import random
import tensorflow as tf
import numpy as np
from PIL import Image
from datetime import datetime
import re
import yfinance as yf
import os
print("Current working directory:", os.getcwd())

# VARIABLEN
mod = input("Model: ")  # CNN-Modell Wahl
model = tf.keras.models.load_model(mod)
folder = input("Chart Folder: ")  # Wahl der Testdaten
x = int(input("Test Sample Size: "))  # Anzahl getestete Charts
c = input("Confidence Treshold: > ")  # Confidence Schwelle
ct = float(c)  # c als Float
tp = float(input("Take Profit (int): "))  # Take Profit in % (übereinstimmend mit Trainings- & Test)
sl = float(input("Stop Loss (int): "))  # Stop Loss in %
d = int(input("Image Size: "))  # Dimension in Pixel
dim = (d, d)  # quadratische Bild mit d x d Pixel



# LABEL EXRAKTION
def extract_label(filename):
    return int(filename.split("label")[1][0])  # Label aus dem Dateinamen herauslesen


# LABEL VOHERSAGE
def predict_chart(image_path):  # Vorhersage mit keras
    img = Image.open(image_path).convert("RGB").resize(dim)  # Pixel werden als RGB-Werte gespeichert
    img_array = np.array(img) / 255.0  # Pixelwerte normalisiert (255 ist schwarz)
    img_array = np.expand_dims(img_array, axis=0)
    p = model.predict(img_array, verbose=0)[0][0]
    pl = int(p >= ct)
    return pl, p

# BILDER LADEN
pngs = [f for f in os.listdir(folder) if f.endswith(".png") and 'label' in f] # .png Files laden
# Dateien innerhalb des gewünschten Ordners mit .png und "label" im Namen
if len(pngs) < x:
    print(f"Not enough images in {folder} (found {len(pngs)}). Need at least 'x'.")
    exit()  # falls die Testmenge die Ordnergrösse übertrifft -> Programmende
sample_files = random.sample(pngs, x)  # x zufällige Charts aus Testdaten wählen


# ZÄHLER
correct_label = 0  # Allgemein korrektes Label
correct_1s = 0  # Korrekt vorhergesagte Label 1
total_predicted_1s = 0  # Anzahl vorhergesagter Label 1
actual_1s = 0  # In der Testmenge vorhandene Label 1

# ANALYTISCHER PROZESS
for file in sample_files:
    full_path = os.path.join(folder, file)
    true_label = int(file.split('label')[1][0])  # das tatsächliche Label (im Namen gespeichert)
    predicted_label, confidence = predict_chart(full_path)

    if predicted_label == 1:  # Label 1 vorhergesagt
        total_predicted_1s += 1  # Zähler für vorhergesagte Label 1
        if true_label == 1:  # Tatsächliches Label = 1
            correct_1s += 1  # Profitable Trades Zähler
    if true_label == 1:  # allgemein falls tatsächliches Label = 1
        actual_1s += 1  # Label 1 Aufkommens Zähler
    if true_label == predicted_label:  # wenn vorhergesagt = tatsächlich
        correct_label += 1  # allgemein korrekte Vorhersagen Zähler


    print(f'Label {predicted_label} predicted with confidence of {confidence} for {file}')


# AUSWERTUNG
print("\n--- Evaluation ---")
label_1_rate = total_predicted_1s / int(x)  # Label 1 Menge / gesamte Menge = Label 1 Vorkommnis
profit = correct_1s * tp - (total_predicted_1s - correct_1s) * sl  # Profitberechnung
# Profitable Trades * TP - Verlorene Trades * SL
actual_1_occurrence = actual_1s / int(x)  # Eigentliche Label 1 Vorkommnisrate
profit_per_tf_unit = profit / int(x)  # Profit pro Datei (=Zeiteinheit)

if total_predicted_1s != 0:
    profit_per_trade = profit / total_predicted_1s  # Profit pro Trade

winrate0 = (correct_label-correct_1s)/ (int(x)-total_predicted_1s)  # Label 0 Erfolgsquote = korrekte 0 / Anzahl vorhergesagte 0
winrate = correct_label / int(x)  # Allgemeine Erfolgsquoten auf Labelvorhersagen


# OUTPUT
print(f"Sample Size: {x}")  # Testdatenmenge
print(f"Confidence Treshold: > {c}")  # Label 1 ^y-Schwelle
print(f"Label 1 Prediction Occurence Rate: {label_1_rate:.2%}")  # Vorkommnis von Label 1 Vorhersagen
print(f'Actual Label 1 Occurence Rate: {actual_1_occurrence: .2%}')  # Vorkommnis von Label 1 in Testmenge

if total_predicted_1s != 0:
    winrate1 = correct_1s / total_predicted_1s  # Label 1 Erfolgsquote
    print(f"Winrate on predicted label 1s: {winrate1:.2%}")
else:
    print("No 1s were predicted.")

print(f'Winrate on Label 0: {winrate0: .2%}')
print(f'Winrate on all Labels: {winrate: .2%}')
print(f'P/L per timeframe unit: {profit_per_tf_unit}%')
print(f'Profit per trade: {profit_per_trade}%')
print(f'Added P/L: {profit}%')


def get_folder_first_last(folder):
    """Return (first_end, last_end, symbol) from chart filenames"""
    chart_files = [f for f in os.listdir(folder)]

    parsed = []
    for f in chart_files:
        match = re.search(r"_(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})_", f)
        if match:
            chart_end = datetime.strptime(match.group(2), "%Y-%m-%d")
            parsed.append((chart_end, f))

    if not parsed:
        return None, None, None

    parsed.sort(key=lambda x: x[0])  # sort by chart end
    first_end = parsed[0][0]
    last_end  = parsed[-1][0]
    symbol = parsed[0][1].split("_")[0]

    return first_end, last_end, symbol


# BUY & HOLD BERECHNUNG
def benchmark_return_from_folder(folder):
    start, end, symbol = get_folder_first_last(folder)
    if not start or not end:
        print(" Could not determine date range from filenames.")
        return None

    df = yf.download(symbol, start=start, end=end, interval="1d",
                     auto_adjust=True, progress=False)
    if df.empty:
        print("No Yahoo data found for benchmark.")
        return None

    first_price = float(df["Close"].iloc[0])  # Preis Beginn Testzeitraum
    last_price = float(df["Close"].iloc[-1])  # Preis Ende Testzeitraum
    ret = (last_price - first_price) / first_price  # Rendite Berechnung
    return ret, symbol, start, end

result = benchmark_return_from_folder(folder)
if result:
    ret, sym, start, end = result
    print(f"\nBuy & Hold {sym}: {ret*100:.2f}% "
          f"(from {start.date()} to {end.date()})")
