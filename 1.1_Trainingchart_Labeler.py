import yfinance as yf
import plotly.graph_objects as go
import datetime
import os
from dateutil.relativedelta import relativedelta


def tp_first_else_zero(data, future_data, f, s):
    if data.empty or future_data.empty or 'Close' not in data:
        return None  # falls kein Preis für den bestimmten Tag abgespeichert ist, überspringen

    base = float(data['Close'].iloc[-1])  # Basispreis
    tp_level = base * (1.0 + float(f))  # Preis bei Take Profit
    sl_level = base * (1.0 - float(s))  # Preis beim Stop Loss

    use_high = 'High' in future_data and not future_data['High'].empty  # Spalte 'High' in yf finden
    use_low = 'Low' in future_data and not future_data['Low'].empty  # Spalte 'Low' in yf finden

    for _, row in future_data.iterrows():  # für jede Kerze, chronologisch
        high = float(row['High']) if use_high else float(row.get('Close', base))  # Hoch = Spalte 'High'
        low = float(row['Low']) if use_low else float(row.get('Close', base))  # Hoch = Spalte 'Low'

        if low <= sl_level:
            return 0  # falls das Tief unter dem SL-Preis liegt -> Label 0
        if high >= tp_level:
            return 1  # falls statt des SL der TP getroffen wurde -> Label 1

    return 0  # falls weder TP oder SL getroffen wurden, Label 0


def generate_and_save_labeled_charts():
    symbols = input("Symbols (comma separated): ").upper().replace(" ", "").split(",")  # Listeneingabe der Aktien
    x = int(input("Charts per symbol per label: "))  # Anzahl Charts pro Label und Symbol
    name = input("Folder name: ")
    cc = input("Use candlechart?: ")  # Kerzenchart benutzen?
    t = str(input("Timeframe: "))  # 1 Kerze repräsentiert t als Zeiteinheit (1d, 1wk, 1mo, 1y)
    u = str(input("Unit of timespan: "))  # Einheit der Zeitspanne
    o = int(input("How many units for the timespan: "))  # Anzahl Einheiten für die Zeitspanne
    w = int(input("Future end in days (best: 7): "))  # Tage bis zum Renditemesstag in der Zukunft
    f = float(input("Take Profit(as fraction): "))  # Take Profit
    s = float(input("Stop loss: "))  # SL-Schwelle für Ausschluss
    d = int(input("Image Dimensions: "))  # Pixeldimensionen für Höhe und Breite, std = 320px
    i1 = int(input( "Last chart ends n time frame units ago: "))  # Anzahl Zeiteinheiten vor dem heutigen Datum, definiert bis wann generiert wird
    # use_ma = input("Use SMA?: ")  # Gleitenden Durchschnitt abbilden?
    # ma = int(input("Moving Average Length: "))  # Länge des gleitenden Durchschnitts
    os.makedirs(name, exist_ok=True)  # Erstellung eines Ordners mit eingegebenen Namen
    # falls der Ordner schon existiert werden die Bilder zu diesem hinzugefügt

    if t == "1d":  # falls die Zeiteinheit 1 Tag ist,
        z = "days"  # Einheit für i
    elif t == "1wk":
        z = "weeks"
    elif t == "1mo":
        z = "weeks"

    for symbol in symbols:  # jedes Symbol (getrennt durch Komma) im Input durchgehen
        ticker = yf.Ticker(symbol)  # Befehl um in der yf-Datenbank die Aktiendaten abzurufen
        label_counts = {0: 0, 1: 0}  # zu Beginn kein Label 0, kein Label 1
        i = i1

        while min(label_counts.values()) < x:  # bis x Charts pro Symbol und Label erstellt wurden
            end_date = datetime.datetime.today() - relativedelta(months=1)  # Enddatum: 1 Monat vor heute
            current_end = end_date - relativedelta(**{z: i})  # erstes Enddatum, definiert durch z & i
            #  z: i bedeutet die Einheit von i (Verschieber) ist die Eingabe von z, ersetzt Format “days = 1“
            current_start = current_end - relativedelta(**{u: o})  # Startdatum, immer 1 Einheit vor Enddatum

            i += 1

            data = ticker.history(start=current_start.strftime('%Y-%m-%d'),
                                  end=current_end.strftime('%Y-%m-%d'),
                                  interval=t)

            # Zukünftige (bzw. 1 Monat nach dem Chart) Preisentwicklung
            future_start = current_end + datetime.timedelta(days=1)  # Beginn des Monats nach dem Chart (Enddatum + 1d)
            future_end = current_end + datetime.timedelta(days=w)  # Zeitpunkt der Renditemessung (1 Monat nch Enddatum)
            future_data = ticker.history(start=future_start.strftime('%Y-%m-%d'),
                                         end=future_end.strftime('%Y-%m-%d'))

            label = 0

            if future_data.empty or data.empty or 'Close' not in future_data or 'Close' not in data:
                continue  # falls keine Daten vorhanden sind, überspringen

            # --- (Preis 1 Monat nach Chartende - Preis bei Chartende) / Preis bei Chartende ---
            # (Kommentar beibehalten; Logik unten ersetzt die reine Endwertprüfung)

            # TP vor SL? → 1, sonst 0 (inkl. "weder noch")
            fh = tp_first_else_zero(data, future_data, f, s)
            if fh is None:
                continue
            if fh == 1 and label_counts[1] < x:
                label = 1
            elif fh == 0 and label_counts[0] < x:
                label = 0
            else:
                continue  # gewünschtes Label schon voll

            # data[f'SMA{str(ma)}'] = data['Close'].rolling(window=ma).mean()  # Berechnung des gleitenden Durchschnitts

            fig = go.Figure()

            if cc == "yes":  # Falls Kerzenchart gewünscht

                fig.add_trace(go.Candlestick(  # Candlestick Charting
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='Candlestick'
                ))

            else:  # Linienchart
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    mode='lines',
                    line=dict(color='black', width=1),
                    name='Close Price'
                ))

            # if use_ma == "yes":  # Gleitender Durchschnitt gewünscht
                # fig.add_trace(go.Scatter(  # MA Konfiguration
                  #  x=data.index,
                   # y=data[f'SMA{str(ma)}'],
                    # mode='lines',
                    #line=dict(color='blue', width=1),
                    # name=f'SMA {str(ma)}'

                #))

            fig.update_layout(  # Sepzifikationen für Layout
                xaxis=dict(visible=False),  # x-Achse unsichtbar
                yaxis=dict(visible=False),  # y-Achse unsichtbar
                showlegend=False,  # Ausblenden der Legende
                margin=dict(l=0, r=0, t=0, b=0),  # keine Ränder
                plot_bgcolor='white',  # Hintergrundfarbe des Chartbereichs
                paper_bgcolor='white',  # Hintergrundfarbe des gesamten Bildes
                xaxis_rangeslider_visible=False,  # Rangeslider aus
                width=d,  # Breite in Pixel, definiert durch Input
                height=d  # Höhe in Pixel, definieret durch denselben Input
            )

            filename = f"{name}/{symbol}_{current_start.date()}_to_{current_end.date()}_label{label}.png"  # Bennenungssystematik
            fig.write_image(filename, format="png", width=d, height=d, scale=1, engine="kaleido")
            label_counts[label] += 1  # Labelzähler für das Label dieses Runs wird um 1 erhöht
            print(f"Saved: {filename} ({label_counts[label]}/{x} for label {label})")

        total = len([f for f in os.listdir(name) if
                     f.endswith(".png") and symbol in f])  # zählt alle .png Files für dieses Symbol
        print(f"Done. Total charts in {name} for {symbol}: {total}")  # Ausgabe Chartanzahl pro Symbol


generate_and_save_labeled_charts()

# Inspiration von: https://ranaroussi.github.io/yfinance/reference/index.html
