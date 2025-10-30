import yfinance as yf
import plotly.graph_objects as go
import datetime
import os
from dateutil.relativedelta import relativedelta


def tp_first_else_zero(data, future_data, f, s):
    if data.empty or future_data.empty or 'Close' not in data:
        return None

    base = float(data['Close'].iloc[-1])
    tp_level = base * (1.0 + float(f))
    sl_level = base * (1.0 - float(s))

    use_high = 'High' in future_data and not future_data['High'].empty
    use_low = 'Low' in future_data and not future_data['Low'].empty
    for _, row in future_data.iterrows():
        high = float(row['High']) if use_high else float(row.get('Close', base))
        low = float(row['Low']) if use_low else float(row.get('Close', base))

        if low <= sl_level:
            return 0
        if high >= tp_level:
            return 1

    return 0


x = int(input("Total charts: "))  # Anzahl Charts pro Label und Symbol


def generate_and_save_labeled_charts():
    symbols = input("Symbols (comma separated): ").upper().replace(" ", "").split(",")  # Listeneingabe der Aktien
    folder_name = input("Folder name: ")
    end_date = datetime.datetime.today() - relativedelta(days=1)  # Enddatum: 1 Monat vor heute
    os.makedirs(folder_name, exist_ok=True)  # Erstellung eines Ordners mit eingegebenen Namen
    # falls der Ordner schon existiert werden die Bilder zu diesem hinzugefügt
    candle_chart = input("Use candlechart?: ")

    t = str(input("Timeframe: "))  # 1 Kerze repräsentiert t als Zeiteinheit (1d, 1wk, 1mo, 1y)
    u = str(input("Unit of timespan: "))  # Einheit der Zeitspanne
    o = int(input("How many units for the timespan: "))  # Anzahl Einheiten für die Zeitspanne
    w = int(input("Future end in days (best: 7): "))  # Tage bis zum Renditemesstag in der Zukunft
    f = float(input("Take Profit(as fraction): "))  # Take Profit
    s = float(input("Stop loss: "))  # SL-Schwelle für Ausschluss
    d = int(input("Image Dimensions: "))  # Pixeldimensionen für Höhe und Breite, std = 320px

    use_ma = input("Use SMA?: ")
    ma = int(input("Moving Average Length: "))  # Länge des gleitenden Durchschnitts

    i1 = int(input(
        "Last chart ends n time frame units ago: "))  # Anzahl Zeiteinheiten vor dem heutigen Datum, definiert bis wann generiert wird

    if t == "1d":  # falls die Zeiteinheit 1 Tag ist,
        z = "days"  # Einheit für i
    elif t == "1wk":
        z = "weeks"
    elif t == "1mo":
        z = "months"

    for symbol in symbols:
        ticker = yf.Ticker(symbol)  # Befehl um in der yf-Datenbank die Aktiendaten abzurufen
        i=i1
        charts_saved = 0
        while charts_saved < x:  # bis x Charts pro Symbol und Label erstellt wurden
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
            if fh == 1:
                label = 1
            elif fh == 0:
                label = 0
            else:
                continue  # gewünschtes Label schon voll

            data[f'SMA{str(ma)}'] = data['Close'].rolling(window=ma).mean()  # Berechnung des gleitenden Durchschnitts

            fig = go.Figure()

            if candle_chart == "yes":

                fig.add_trace(go.Candlestick(  # Candlestick Charting
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='Candlestick'
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    mode='lines',
                    line=dict(color='black', width=1),
                    name='Close Price'
                ))

            if use_ma == "yes":
                fig.add_trace(go.Scatter(  # MA Konfiguration
                    x=data.index,
                    y=data[f'SMA{str(ma)}'],
                    mode='lines',
                    line=dict(color='blue', width=1),
                    name=f'SMA {str(ma)}'

                ))

            fig.update_layout(
                xaxis=dict(visible=False),  # x-Achse unsichtbar
                yaxis=dict(visible=False),  # y-Achse unsichtbar
                showlegend=False,  # Ausblenden der Legende
                margin=dict(l=0, r=0, t=0, b=0),  # keine Ränder
                plot_bgcolor='white',  # Hintergrundfarbe des Chartbereichs
                paper_bgcolor='white',  # Hintergrundfarbe des gesamten Bildes
                xaxis_rangeslider_visible=False,  # Rangeslider aus
                width=d,  # Breite in Pixel, definiert durch Input
                height=d  # Höhe in Pixel, definiert durch denselben Input
            )

            filename = f"{folder_name}/{symbol}_{current_start.date()}_to_{current_end.date()}_label{label}.png"
            fig.write_image(filename, format="png", width=d, height=d, scale=1, engine="kaleido")

            charts_saved += 1  # Labelzähler für das Label dieses Runs wird um 1 erhöht
            print(f"Saved: {filename} ({charts_saved}/{x})")

        total = len([f for f in os.listdir(folder_name) if
                     f.endswith(".png") and symbol in f])  # zählt alle .png Files für dieses Symbol
        print(f"Done. Total charts in {folder_name} for {symbol}: {total}")  # Ausgabe Chartanzahl pro Symbol


generate_and_save_labeled_charts()
