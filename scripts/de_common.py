"""Gemeinsame Teile für den Export der deutschen Produkte (CSV- und JSONL-Leser).

Ausgabeformat „tb1“ (gzip, eine Zeile pro Produkt, Tab-getrennt):
    code, Name, Marke, Menge, Einheit (g|ml), kcal, Eiweiß, Kohlenhydrate, Fett je 100 g/ml, Portion (g/ml), Bild
Erste Zeile: „#tb1“ und die Spaltennamen. Reihenfolge: in Deutschland beliebteste Produkte zuerst (siehe rank_score).
Die Daten stammen von Open Food Facts und stehen unter der Open Database License (ODbL) 1.0.
"""
import collections, datetime, gzip, hashlib, json, math, os, re, sys, time

FORMAT = ['code', 'n', 'b', 'q', 'u', 'k', 'p', 'c', 'f', 'sv', 'img']
VERSION_LINE = '#tb1\t' + '\t'.join(FORMAT)

# Marken stehen im Export teils nur als Kennung („xx:gut-gunstig“). Für häufige Marken die richtige Schreibweise.
BRAND_NAMES = {
    'gut-gunstig': 'Gut & Günstig', 'gut-und-gunstig': 'Gut & Günstig', 'ja': 'ja!', 'k-classic': 'K-Classic', 'k-bio': 'K-Bio',
    'k-favourites': 'K-Favourites', 'k-to-go': 'K-to-go', 'rewe-beste-wahl': 'REWE Beste Wahl', 'rewe-bio': 'REWE Bio', 'rewe': 'REWE',
    'rewe-feine-welt': 'REWE Feine Welt', 'rewe-frei-von': 'REWE frei von', 'edeka': 'EDEKA', 'edeka-bio': 'EDEKA Bio',
    'edeka-herzstucke': 'EDEKA Herzstücke', 'edeka-italia': 'EDEKA Italia', 'dmbio': 'dmBio', 'dm-bio': 'dmBio', 'gutbio': 'GutBio',
    'enerbio': 'enerBiO', 'fin-carre': 'Fin Carré', 'rio-d-oro': "Rio d'Oro", 'dr-oetker': 'Dr. Oetker', 'coca-cola': 'Coca-Cola',
    'mullermilch': 'Müllermilch', 'muller': 'Müller', 'kolln': 'Kölln', 'hohes-c': 'Hohes C', 'lidl': 'Lidl', 'aldi': 'ALDI',
    'aldi-sud': 'ALDI SÜD', 'aldi-nord': 'ALDI Nord', 'penny': 'PENNY', 'netto': 'Netto', 'kaufland': 'Kaufland', 'norma': 'NORMA',
    'alnatura': 'Alnatura', 'goldahren': 'Goldähren', 'barenmarke': 'Bärenmarke', 'lowensenf': 'Löwensenf', 'kuhne': 'Kühne',
    'nestle': 'Nestlé', 'ritter-sport': 'Ritter Sport', 'frosta': 'FRoSTA', 'rugenwalder-muhle': 'Rügenwalder Mühle',
    'kellogg-s': "Kellogg's", 'kelloggs': "Kellogg's", 'golden-toast': 'Golden Toast', 'lieken-urkorn': 'Lieken Urkorn',
    'berchtesgadener-land': 'Berchtesgadener Land', 'simply-v': 'Simply V', 'garden-gourmet': 'Garden Gourmet', 'capri-sun': 'Capri-Sun',
    'red-bull': 'Red Bull', 'milsani': 'Milsani', 'milbona': 'Milbona', 'moser-roth': 'Moser Roth', 'cucina-nobile': 'Cucina Nobile',
    'chef-select': 'Chef Select', 'trader-joe-s': "Trader Joe's", 'tegut': 'tegut', 'globus': 'Globus', 'aro': 'ARO', 'dm': 'dm',
}
# Eigene Zuordnung von Handelsmarken zu Händlern (nur für den Bericht). Kennungen ohne „xx:“.
RETAIL = {
    'Lidl': ['lidl', 'milbona', 'pilos', 'solevita', 'crownfield', 'fin-carre', 'chef-select', 'vemondo', 'kania', 'alesto', 'snack-day',
             'freeway', 'sondey', 'combino', 'deluxe', 'vitasia', 'italiamo', 'eridanous', 'baresa', 'nixe', 'ocean-sea', 'dulano',
             'mcennedy', 'sol-mar', 'bellarom', 'trattoria-alfredo', 'favorina', 'golden-sun', 'grafschafter', 'harvest-basket',
             'perlenbacher', 'linessa', 'envia', 'cowbelle', 'next-level-meat', 'gelatelli', 'freshona', 'metzgerfrisch', 'w5',
             'carre-fin-lidl', 'chef-select-you', 'bio-organic', 'vitafit', 'pikok', 'sanetta', 'saskia', 'jeden-tag-lidl'],
    'Aldi': ['aldi', 'aldi-sud', 'aldi-nord', 'milsani', 'moser-roth', 'gutbio', 'rio-d-oro', 'cucina-nobile', 'choceur', 'knusperone',
             'golden-bridge', 'lyttos', 'farmer', 'asia-green-garden', 'river', 'goldahren', 'meine-metzgerei', 'sweet-valley', 'belbake',
             'almare', 'gut-drei-eichen', 'cantinetta', 'nur-nur-natur', 'mama-mancini', 'bon-gelati', 'kokett', 'trader-joe-s',
             'casa-morando', 'la-finesse', 'park-street-deli', 'snackfun', 'happy-harvest', 'deli-reform', 'feine-welt', 'tukan',
             'mucci', 'sun-snacks', 'westminster', 'just-veg', 'gourmet', 'wonnemeyer', 'lacura'],
    'Rewe/Penny': ['rewe', 'ja', 'rewe-beste-wahl', 'rewe-bio', 'rewe-feine-welt', 'rewe-frei-von', 'rewe-to-go', 'penny', 'naturgut',
                   'food-for-future', 'penny-ready', 'san-fabio', 'wilhelm-brandenburg', 'rewe-regional', 'bio-wertkost'],
    'Edeka/Netto': ['edeka', 'gut-gunstig', 'gut-und-gunstig', 'edeka-bio', 'edeka-herzstucke', 'edeka-italia', 'edeka-zuhause',
                    'edeka-genussmomente', 'netto', 'mein-veggie-tag', 'biobio', 'bio-bio', 'gut-bio', 'gutes-land', 'marktkauf', 'kunella'],
    'Kaufland': ['kaufland', 'k-classic', 'k-bio', 'k-favourites', 'k-to-go', 'k-take-it-veggie', 'k-free', 'exquisit'],
    'dm': ['dm', 'dmbio', 'dm-bio', 'mivolis', 'das-gesunde-plus', 'sana-sana'],
    'Rossmann': ['rossmann', 'enerbio', 'altapharma', 'babydream'],
    'Norma': ['norma', 'gourmet-finest-cuisine', 'tradition', 'mama-s-pasta'],
    'Globus': ['globus'],
    'tegut': ['tegut', 'tegut-bio'],
    'Metro': ['aro', 'metro-chef', 'metro-premium'],
}

LIQUID = re.compile(r'\d\s*(ml|cl|dl|l)\b', re.I)
SOLID = re.compile(r'\d\s*(g|kg)\b', re.I)
IMG_PRE = 'https://images.openfoodfacts.org/images/products/'
POP_TOP = re.compile(r'^top-(\d+)-de-scans-(\d{4})$')
POP_MIN = re.compile(r'^at-least-(\d+)-de-scans-(\d{4})$')
BUCKET = {10: 9, 50: 8, 100: 7, 500: 6, 1000: 5, 5000: 4, 10000: 3, 50000: 2, 100000: 1}


def clean(s, n):
    if s is None:
        return ''
    s = re.sub(r'\s+', ' ', str(s).replace('\t', ' ')).strip()
    return s[:n]


def num(s):
    if isinstance(s, bool) or s is None:
        return None
    if isinstance(s, (int, float)):
        v = float(s)
    else:
        s = str(s).strip().replace(',', '.')
        if not s:
            return None
        try:
            v = float(s)
        except ValueError:
            return None
    return v if v == v and abs(v) != float('inf') else None


def fmt(v, d):
    if v is None:
        return ''
    r = round(v, d)
    if d == 0 or r == int(r):
        return str(int(round(r)))
    return ('%.' + str(d) + 'f') % r


def tag_id(t):
    t = (t or '').strip().lower()
    return re.sub(r'^[a-z]{2}:', '', t)


def brand_from_tag(t):
    tid = tag_id(t)
    if not tid:
        return ''
    if tid in BRAND_NAMES:
        return BRAND_NAMES[tid]
    return ' '.join(w[:1].upper() + w[1:] for w in tid.split('-') if w)


def img_path(code):
    c = code.rjust(13, '0')
    return c[0:3] + '/' + c[3:6] + '/' + c[6:9] + '/' + c[9:]


def img_key(code, url):
    """Aus einer Bild-URL den kurzen Schlüssel machen (die App setzt die URL wieder zusammen)."""
    url = (url or '').strip()
    if not url.startswith(IMG_PRE) or not url.endswith('.jpg'):
        return ''
    rest = url[len(IMG_PRE):-4]
    p = img_path(code) + '/'
    return rest[len(p):] if rest.startswith(p) else rest


def unit_from_qty(qty):
    return 'ml' if LIQUID.search(qty or '') and not SOLID.search(qty or '') else 'g'


def de_pop(tags):
    """Beliebtheit in Deutschland aus den popularity_tags (alle Jahre): bester Rang, Mindest-Scans, meistgescannt in DE."""
    best = least = 0
    topc = False
    for t in tags or []:
        t = str(t)
        m = POP_TOP.match(t)
        if m:
            best = max(best, BUCKET.get(int(m.group(1)), 0))
            continue
        m = POP_MIN.match(t)
        if m:
            least = max(least, int(m.group(1)))
            continue
        if t.startswith('top-country-de-scans-'):
            topc = True
    return best, least, topc


def rank_score(best, least, topc, lang_de, name_de, scans):
    """Höher = weiter vorn. In Deutschland oft gescannt zählt am meisten, dann deutsche Hauptsprache und deutscher Name."""
    return (best * 10 + (6 if least >= 10 else 3 if least >= 5 else 0) + (8 if topc else 0)
            + (25 if lang_de else 0) + (10 if name_de else 0) + 5 * math.log10(1 + max(0.0, scans or 0)))


class Collector:
    def __init__(self, source):
        self.source = source
        self.st = collections.Counter()
        self.brands = collections.Counter()
        self.shop_of = {i: shop for shop, ids in RETAIL.items() for i in ids}
        self.shops = collections.Counter()
        self.shop_brand = collections.defaultdict(collections.Counter)
        self.rows = []
        self.seen = set()
        self.t0 = time.time()

    def add(self, code, name, brand, btags, qty, unit, kcal, mac, sv, img, score):
        """Prüft und übernimmt ein Produkt. Gibt den Grund zurück, falls es aussortiert wird."""
        code = re.sub(r'\D', '', code or '')
        if len(code) < 6 or len(code) > 14 or code in self.seen:
            self.st['ohne_code'] += 1
            return
        if not name:
            self.st['ohne_name'] += 1
            return
        if kcal is None:
            self.st['ohne_kalorien'] += 1
            return
        if not (0 <= kcal <= 950):
            self.st['kalorien_unplausibel'] += 1
            return
        if any(v is not None and not (0 <= v <= 100) for v in mac):
            self.st['naehrwerte_unplausibel'] += 1
            return
        sv = sv if sv is not None and 0 < sv <= 2000 else None
        self.seen.add(code)
        bids = [tag_id(t) for t in btags[:3] if t]
        for b in bids:
            self.brands[b] += 1
        mine = {}
        for b in bids:
            if b in self.shop_of and self.shop_of[b] not in mine:
                mine[self.shop_of[b]] = b
        for shop, b in mine.items():
            self.shops[shop] += 1
            self.shop_brand[shop][b] += 1
        if mine:
            self.st['handelsmarke'] += 1
        self.rows.append((-round(score, 3), code, '\t'.join([code, clean(name, 80), clean(brand, 40), clean(qty, 30), unit, fmt(kcal, 0),
                                                              fmt(mac[0], 1), fmt(mac[1], 1), fmt(mac[2], 1), fmt(sv, 1), img])))
        self.st['behalten'] += 1

    def write(self, out, extra=None):
        st, rows = self.st, self.rows
        if st['behalten'] < 50000 and not os.environ.get('TB_TEST'):
            sys.exit('Zu wenige Produkte (%d). Export kaputt oder Format geändert? Zähler: %s' % (st['behalten'], dict(st)))
        os.makedirs(out, exist_ok=True)
        rows.sort()
        now = datetime.datetime.now(datetime.timezone.utc)
        data = (VERSION_LINE + '\n' + '\n'.join(r[2] for r in rows) + '\n').encode('utf-8')
        gz = gzip.compress(data, compresslevel=9, mtime=0)
        # Name mit Prüfsumme: jede neue Fassung hat eine eigene Adresse (kein veralteter Zwischenspeicher, auch zweimal am Tag)
        fname = 'de-%s-%s.tsv.gz' % (now.strftime('%Y%m%d'), hashlib.sha256(gz).hexdigest()[:8])
        with open(os.path.join(out, fname), 'wb') as fh:
            fh.write(gz)
        v = now.strftime('%Y-%m-%d')
        man = {'format': 'tb1', 'v': v, 'file': fname, 'n': len(rows), 'bytes': len(gz), 'raw': len(data),
               'sha256': hashlib.sha256(gz).hexdigest(), 'quelle': 'Open Food Facts (https://world.openfoodfacts.org), ODbL 1.0'}
        with open(os.path.join(out, 'manifest.json'), 'w', encoding='utf-8') as fh:
            json.dump(man, fh, ensure_ascii=False, indent=1)
        ret = {shop: {'summe': self.shops[shop], 'marken': [[brand_from_tag(i), c] for i, c in self.shop_brand[shop].most_common()]} for shop in RETAIL}
        rep = {'stand': v, 'quelle': self.source, 'datei': fname, 'mb': round(len(gz) / 1e6, 1), 'mb_entpackt': round(len(data) / 1e6, 1),
               'zaehler': dict(st), 'sekunden': round(time.time() - self.t0), 'top_marken': [[brand_from_tag(i), c] for i, c in self.brands.most_common(80)],
               'handel': ret, 'erste_50': [r[2].split('\t')[1] + ' · ' + r[2].split('\t')[2] for r in rows[:50]]}
        if extra:
            rep.update(extra)
        with open(os.path.join(out, 'report.json'), 'w', encoding='utf-8') as fh:
            json.dump(rep, fh, ensure_ascii=False, indent=1)
        md = ['# Deutsche Produkte, Stand %s' % v, '',
              '- Produkte in der Datei: **%d** (%s MB gepackt, %s MB entpackt)' % (len(rows), rep['mb'], rep['mb_entpackt']),
              '- Quelle: %s, Laufzeit %d s' % (self.source, rep['sekunden']),
              '- Gelesen: %d, davon Deutschland: %d' % (st['gelesen'], st['deutschland']),
              '- Aussortiert: ohne Kalorien %d, ohne Name %d, ohne Barcode %d, unplausibel %d' % (
                  st['ohne_kalorien'], st['ohne_name'], st['ohne_code'], st['kalorien_unplausibel'] + st['naehrwerte_unplausibel'])]
        if st['name_de'] or st['name_andere']:
            md.append('- Namen: deutsch %d, andere Sprache %d' % (st['name_de'], st['name_andere']))
        md += ['', '## Handelsmarken (eigene Zuordnung, %d Produkte)' % st['handelsmarke'], '']
        for shop, r in ret.items():
            md.append('- **%s**: %d Produkte. %s' % (shop, r['summe'], ', '.join('%s %d' % (b, c) for b, c in r['marken'][:12])))
        md += ['', '## Häufigste Marken', '']
        md += ['%d. %s: %d' % (i + 1, b, c) for i, (b, c) in enumerate(rep['top_marken'][:60])]
        md += ['', '## Die 50 ersten Produkte der Datei', ''] + ['%d. %s' % (i + 1, x) for i, x in enumerate(rep['erste_50'])]
        md += ['', 'Daten: Open Food Facts, Open Database License (ODbL) 1.0.', '']
        with open(os.path.join(out, 'report.md'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(md))
        print('\n'.join(md[:9]))
