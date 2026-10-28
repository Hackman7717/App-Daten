# App-Daten

Lebensmitteldaten für die [Trainingsbuch-App](https://github.com/Hackman7717/App): ein Auszug aus
[Open Food Facts](https://world.openfoodfacts.org) mit allen Produkten, die in Deutschland verkauft werden
und Kalorienangaben haben. Die App lädt die Datei einmal herunter und sucht danach auf dem Gerät, sofort und ohne Internet.

## So funktioniert es

- Die GitHub-Aufgabe [`daten.yml`](.github/workflows/daten.yml) läuft jeden Montag um 02:23 UTC (und bei Änderungen an Skripten).
- Sie lädt den täglichen Export von Open Food Facts (`en.openfoodfacts.org.products.csv.gz`, etwa 0,9 GB),
  filtert mit [`scripts/build_de.py`](scripts/build_de.py) und veröffentlicht das Ergebnis im Zweig `gh-pages`:
  - `de-JJJJMMTT.tsv.gz`: die Produkte, beliebteste zuerst
  - `manifest.json`: Stand, Dateiname, Anzahl, Größe, SHA-256
  - `report.md`: Zahlen, Handelsmarken und häufigste Marken
- Der Zweig `gh-pages` enthält immer nur den neuesten Stand und die vorige Datei, damit das Repository nicht wächst.
- Den letzten Bericht gibt es auch hier unter [`report/report.md`](report/report.md).

## Was drin ist

Ein Produkt wird übernommen, wenn seine Länder Deutschland enthalten, es einen Namen hat und Kalorien pro 100 g oder ml
angegeben sind (0 bis 950 kcal). Eiweiß, Kohlenhydrate und Fett dürfen fehlen. Pro Produkt: Barcode, Name, Marke, Menge,
Einheit (g oder ml), kcal, Eiweiß, Kohlenhydrate, Fett, Portion und ein Verweis auf das Produktbild.

## Lizenz

Diese Datenbank enthält Informationen aus Open Food Facts, die unter der
[Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/) bereitgestellt werden.
Der Auszug steht ebenfalls unter der ODbL, einzelne Inhalte unter der
[Database Contents License (DbCL) 1.0](https://opendatacommons.org/licenses/dbcl/1-0/). Die Skripte in diesem Repository
dürfen frei verwendet werden.
