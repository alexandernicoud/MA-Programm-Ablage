**Maturaarbeit – KI-Trading-Bot (CNN)**

Dieses Projekt entstand im Rahmen der Maturaarbeit an der Kantonsschule Wettingen.
Ziel war die Entwicklung eines Convolutional Neural Networks (CNN), das anhand von Candlestick-Charts Kursbewegungen von in Echtzeit Aktien vorhersagt.

**Projektidee**

Das System nutzt automatisch generierte Chartbilder als Eingabe für ein neuronales Netz.
Das CNN wird darauf trainiert, steigende (Label 1) und fallende (Label 0) Kursverläufe zu unterscheiden.

Projektstruktur

1.1_Trainingchart_Labler.py – plotted, labelt und speichert Trainingscharts mit yfinance-Daten

1.2_Testchart_Labler.py – plotted, labelt und speichert historische Testcharts zur Evaluation

2_Trainer.py – trainiert das CNN-Modell (Keras) anhand der Trainingscharts

3_predict_chart_winrate.py – backtestet das Modell anhand der Testcharts, berechnet relevante Metriken wie Winrate und Added P/L

4_tradingbot.py – analysiert täglich nach Börsenschluss den aktuellen Graphen und versendet eine Telegram-Benachrichtigungen mit der Label-Vorhersage


**Anforderungen**

Python 3.10 oder neuer
Folgende Bibliotheken müssen installiert sein:

pip install yfinance pandas numpy matplotlib ta tensorflow scikit-learn plotly


**Verwendung**

Backtesting:

1) Programm 1.1 starten und gewünschte Parameterinputs ausfüllen
   -> Plotten, Labeln und Speichern beliebiger Anzahl Charts
   Bemerkung: Genau den Input-Anweisungen folgen, da die Eingaben dem Format entsprechen müssen
   Bemerkung: Falls die KI Backtesting braucht, ist es sinnvoll den Testzeitraum NICHT plotten zu lassen (sonst sind keine "ungesehenen Charts" für das Backtesting übrig)
   
2) Programm 2 starten und gewünschte Parameterinputs ausfüllen
   -> Ein Keras Modell wird trainiert und gespeichert

3) Programm 1.2 starten und gewünschte Parameterinputs ausfüllen
   -> Plotten, Labeln und Speichern
   Bemerkung: Den nicht abgedeckten Zeitraum der Trainingscharts ist der Testchart-Zeitraum. Es soll keine zeitliche Überschneidung geben
   Bemerkung: Es ist grundsätzlich sinnvoll dieselben Einstellungen, wie für die Trainingscharts verwendet wurden, zu übernehmen

4) Programm 3 starten und Test-Modell auswählend sowie den Ordner mit den TESTcharts


**Autor**

Alexander Nicoud
Kantonsschule Wettingen
Maturaarbeit 2024/25
Betreuung: Andreia Venzin
