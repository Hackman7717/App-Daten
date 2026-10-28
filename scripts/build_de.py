#!/usr/bin/env python3
"""Deutsche Produkte aus dem täglichen Open-Food-Facts-Export für die Trainingsbuch-App.

Eingabe:  der entpackte CSV-Export (Tab-getrennt, erste Zeile Spaltennamen) über stdin,
          z. B. curl … en.openfoodfacts.org.products.csv.gz | gunzip -c | python3 build_de.py out
Ausgabe:  out/de-JJJJMMTT.tsv.gz   Produkte, beliebteste zuerst (siehe FORMAT)
          out/manifest.json        Version, Datei, Anzahl, Größe, SHA-256
          out/report.json, out/report.md   Zahlen und häufigste Marken

Behalten wird ein Produkt, wenn
  - seine Länder „en:germany“ enthalten,
  - es einen Namen hat,
  - Kalorien pro 100 g/ml angegeben sind (direkt oder aus kJ) und plausibel sind (0 bis 950 kcal).
Eiweiß, Kohlenhydrate und Fett dürfen fehlen (leer), Werte über 100 g werden verworfen.

Die Daten stammen von Open Food Facts und stehen unter der Open Database License (ODbL) 1.0.
"""
import collections, datetime, gzip, hashlib, json, os, re, sys, time

FORMAT = ['code', 'n', 'b', 'q', 'u', 'k', 'p', 'c', 'f', 'sv', 'img']
VERSION_LINE = '#tb1\t' + '\t'.join(FORMAT)

# Marken stehen im Export (seit 2026) nur noch als Kennung, z. B. „xx:gut-gunstig“. Für häufige Marken die richtige Schreibweise.
BRAND_NAMES = {
    'gut-gunstig': 'Gut & Günstig', 'gut-und-gunstig': 'Gut & Günstig', 'ja': 'ja!', 'k-classic': 'K-Classic', 'k-bio': 'K-Bio',
    'k-favourites': 'K-Favourites', 'k-to-go': 'K-to-go', 'rewe-beste-wahl': 'REWE Beste Wahl', 'rewe-bio': 'REWE Bio', 'rewe': 'REWE',
    'rewe-feine-welt': 'REWE Feine Welt', 'rewe-frei-von': 'REWE frei von', 'edeka': 'EDEKA', 'edeka-bio': 'EDEKA Bio',
    'edeka-herzstucke': 'EDEKA Herzstücke', 'edeka-italia': 'EDEKA Italia', 'dmbio': 'dmBio', 'dm-bio': 'dmBio', 'gutbio': 'GutBio',
    'enerbio': 'enerBiO', 'fin-carre': 'Fin Carré', 'rio-d-oro': "Rio d'Oro", 'dr-oetker': 'Dr. Oetker', 'coca-cola': 'Coca-Cola',
    'mullermilch': 'Müllermilch', 'muller': 'Müller', 'kolln': 'Kölln', 'hohes-c': 'Hohes C', 'mondamin': 'Mondamin', 'lidl': 'Lidl',
    'aldi': 'ALDI', 'aldi-sud': 'ALDI SÜD', 'aldi-nord': 'ALDI Nord', 'penny': 'PENNY', 'netto': 'Netto', 'kaufland': 'Kaufland',
    'norma': 'NORMA', 'alnatura': 'Alnatura', 'goldahren': 'Goldähren', 'baren-marke': 'Bärenmarke', 'barenmarke': 'Bärenmarke',
    'lowensenf': 'Löwensenf', 'kuhne': 'Kühne', 'bahlsen': 'Bahlsen', 'haribo': 'Haribo', 'nestle': 'Nestlé', 'nutella': 'Nutella',
    'ferrero': 'Ferrero', 'milka': 'Milka', 'ritter-sport': 'Ritter Sport', 'knorr': 'Knorr', 'maggi': 'Maggi', 'iglo': 'iglo',
    'frosta': 'FRoSTA', 'zott': 'Zott', 'ehrmann': 'Ehrmann', 'weihenstephan': 'Weihenstephan', 'arla': 'Arla', 'danone': 'Danone',
    'alpro': 'Alpro', 'oatly': 'Oatly', 'rugenwalder-muhle': 'Rügenwalder Mühle', 'meica': 'Meica', 'herta': 'Herta',
    'wiesenhof': 'Wiesenhof', 'barilla': 'Barilla', 'seitenbacher': 'Seitenbacher', 'leibniz': 'Leibniz', 'lorenz': 'Lorenz',
    'funny-frisch': 'funny-frisch', 'chio': 'Chio', 'pringles': 'Pringles', 'kellogg-s': "Kellogg's", 'kelloggs': "Kellogg's",
    'mymuesli': 'mymuesli', 'golden-toast': 'Golden Toast', 'harry': 'Harry', 'lieken-urkorn': 'Lieken Urkorn', 'milram': 'Milram',
    'bresso': 'Bresso', 'philadelphia': 'Philadelphia', 'leerdammer': 'Leerdammer', 'gouda': 'Gouda', 'landliebe': 'Landliebe',
    'andechser-natur': 'Andechser Natur', 'berchtesgadener-land': 'Berchtesgadener Land', 'schwarzwaldmilch': 'Schwarzwaldmilch',
    'hochland': 'Hochland', 'simply-v': 'Simply V', 'garden-gourmet': 'Garden Gourmet', 'like-meat': 'Like Meat', 'valensina': 'Valensina',
    'capri-sun': 'Capri-Sun', 'red-bull': 'Red Bull', 'fritz-kola': 'fritz-kola', 'gerolsteiner': 'Gerolsteiner', 'volvic': 'Volvic',
    'milsani': 'Milsani', 'milbona': 'Milbona', 'moser-roth': 'Moser Roth', 'cucina-nobile': 'Cucina Nobile', 'chef-select': 'Chef Select',
}
# Eigene Zuordnung von Handelsmarken zu Händlern (nur für den Bericht). Kennungen ohne „xx:“.
RETAIL = {
    'Lidl': ['lidl', 'milbona', 'pilos', 'solevita', 'crownfield', 'fin-carre', 'chef-select', 'vemondo', 'kania', 'alesto', 'snack-day',
             'freeway', 'sondey', 'combino', 'deluxe', 'vitasia', 'italiamo', 'eridanous', 'baresa', 'nixe', 'ocean-sea', 'dulano',
             'mcennedy', 'sol-mar', 'bellarom', 'trattoria-alfredo', 'favorina', 'golden-sun', 'grafschafter', 'harvest-basket',
             'perlenbacher', 'linessa', 'envia', 'bio-organic', 'cowbelle', 'chef-select-you', 'next-level-meat', 'gelatelli', 'tastino'],
    'Aldi': ['aldi', 'aldi-sud', 'aldi-nord', 'milsani', 'moser-roth', 'gutbio', 'rio-d-oro', 'cucina-nobile', 'choceur', 'knusperone',
             'golden-bridge', 'lyttos', 'farmer', 'asia-green-garden', 'river', 'goldahren', 'meine-metzgerei', 'sweet-valley', 'belbake',
             'almare', 'gut-drei-eichen', 'cantinetta', 'nur-nur-natur', 'mama-mancini', 'bon-gelati', 'kokett', 'brandt-and-co',
             'trader-joe-s', 'casa-morando', 'la-finesse', 'mucci', 'sun-snacks', 'ombra', 'workout', 'wonnemeyer', 'lacura', 'tukan',
             'park-street-deli', 'snackfun', 'happy-harvest', 'deli-reform', 'feine-welt'],
    'Rewe/Penny': ['rewe', 'ja', 'rewe-beste-wahl', 'rewe-bio', 'rewe-feine-welt', 'rewe-frei-von', 'rewe-to-go', 'penny', 'naturgut',
                   'food-for-future', 'penny-ready', 'san-fabio', 'wilhelm-brandenburg', 'rewe-regional', 'bio-wertkost'],
    'Edeka/Netto': ['edeka', 'gut-gunstig', 'gut-und-gunstig', 'edeka-bio', 'edeka-herzstucke', 'edeka-italia', 'edeka-zuhause',
                    'edeka-genussmomente', 'netto', 'mein-veggie-tag', 'bio-bio', 'gut-bio', 'marktkauf', 'kunella'],
    'Kaufland': ['kaufland', 'k-classic', 'k-bio', 'k-favourites', 'k-to-go', 'k-take-it-veggie', 'k-free', 'exquisit'],
    'dm': ['dm', 'dmbio', 'dm-bio', 'mivolis', 'das-gesunde-plus', 'sana-sana'],
    'Rossmann': ['rossmann', 'enerbio', 'altapharma', 'babydream'],
    'Norma': ['norma', 'gourmet-finest-cuisine', 'tradition', 'mama-s-pasta'],
}

LIQUID = re.compile(r'\d\s*(ml|cl|dl|l)\b', re.I)
SOLID = re.compile(r'\d\s*(g|kg)\b', re.I)


def clean(s, n):
    s = re.sub(r'\s+', ' ', (s or '').replace('\t', ' ')).strip()
    return s[:n]


def num(s):
    s = (s or '').strip().replace(',', '.')
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
    words = [w for w in tid.split('-') if w]
    return ' '.join(w[:1].upper() + w[1:] for w in words)


def img_path(code):
    c = code.rjust(13, '0')
    return c[0:3] + '/' + c[3:6] + '/' + c[6:9] + '/' + c[9:]


IMG_PRE = 'https://images.openfoodfacts.org/images/products/'


def img_key(code, url):
    url = (url or '').strip()
    if not url.startswith(IMG_PRE) or not url.endswith('.jpg'):
        return ''
    rest = url[len(IMG_PRE):-4]
    p = img_path(code) + '/'
    return rest[len(p):] if rest.startswith(p) else rest


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'out'
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    inp = sys.stdin.buffer
    header = inp.readline().decode('utf-8', 'replace').rstrip('\r\n').split('\t')
    H = {name: i for i, name in enumerate(header)}

    def col(*names, need=False):
        for nm in names:
            if nm in H:
                return H[nm], nm
        if need:
            sys.exit('Spalte fehlt im Export: ' + ' oder '.join(names) + '\nVorhanden: ' + ', '.join(header[:80]))
        return None, None

    i_code, _ = col('code', need=True)
    i_name, _ = col('product_name', need=True)
    i_gen, _ = col('generic_name')
    i_ctry, ctry_col = col('countries_tags', 'countries', need=True)
    i_brand, brand_col = col('brands', 'brands_tags')
    i_btags, _ = col('brands_tags')
    i_qty, _ = col('quantity')
    i_svq, _ = col('serving_quantity')
    i_kcal, _ = col('energy-kcal_100g')
    i_kj, _ = col('energy-kj_100g')
    i_en, _ = col('energy_100g')
    if i_kcal is None and i_kj is None and i_en is None:
        sys.exit('Keine Energie-Spalte im Export gefunden.')
    i_p, _ = col('proteins_100g')
    i_c, _ = col('carbohydrates_100g')
    i_f, _ = col('fat_100g')
    i_scan, _ = col('unique_scans_n')
    i_img, _ = col('image_small_url', 'image_front_small_url')
    need = max(i for i in [i_code, i_name, i_ctry] if i is not None)

    st = collections.Counter()
    brands = collections.Counter()
    shop_of = {i: shop for shop, ids in RETAIL.items() for i in ids}
    shops = collections.Counter()
    shop_brand = collections.defaultdict(collections.Counter)
    rows = []
    seen = set()
    for raw in inp:
        st['zeilen'] += 1
        if b'en:germany' not in raw:
            continue
        f = raw.decode('utf-8', 'replace').rstrip('\r\n').split('\t')
        if len(f) <= need:
            st['kaputt'] += 1
            continue
        g = lambda i: f[i] if i is not None and i < len(f) else ''
        if 'en:germany' not in g(i_ctry).split(','):
            continue
        st['deutschland'] += 1
        code = re.sub(r'\D', '', g(i_code))
        if len(code) < 6 or len(code) > 14 or code in seen:
            st['ohne_code'] += 1
            continue
        name = clean(g(i_name), 80) or clean(g(i_gen), 80)
        if not name:
            st['ohne_name'] += 1
            continue
        k = num(g(i_kcal))
        if k is None:
            kj = num(g(i_kj))
            if kj is None:
                kj = num(g(i_en))
            k = kj / 4.184 if kj is not None else None
        if k is None:
            st['ohne_kalorien'] += 1
            continue
        if not (0 <= k <= 950):
            st['kalorien_unplausibel'] += 1
            continue
        mac = [num(g(i)) for i in (i_p, i_c, i_f)]
        if any(v is not None and not (0 <= v <= 100) for v in mac):
            st['naehrwerte_unplausibel'] += 1
            continue
        btags = [t for t in g(i_btags).split(',') if t.strip()] if i_btags is not None else []
        if brand_col == 'brands':
            brand = clean(g(i_brand).split(',')[0], 40)
        else:
            brand = clean(brand_from_tag(btags[0]) if btags else '', 40)
        qty = clean(g(i_qty), 30)
        unit = 'ml' if LIQUID.search(qty) and not SOLID.search(qty) else 'g'
        sv = num(g(i_svq))
        sv = sv if sv is not None and 0 < sv <= 2000 else None
        scans = num(g(i_scan)) or 0
        seen.add(code)
        bids = [tag_id(t) for t in btags[:3]]
        for b in bids:
            brands[b] += 1
        mine = {}
        for b in bids:
            if b in shop_of and shop_of[b] not in mine:
                mine[shop_of[b]] = b
        for shop, b in mine.items():
            shops[shop] += 1
            shop_brand[shop][b] += 1
        if mine:
            st['handelsmarke'] += 1
        rows.append((-scans, code, '\t'.join([code, name, brand, qty, unit, fmt(k, 0), fmt(mac[0], 1), fmt(mac[1], 1), fmt(mac[2], 1),
                                              fmt(sv, 1), img_key(code, g(i_img))])))
        st['behalten'] += 1

    if st['behalten'] < 1000:
        sys.exit('Zu wenige Produkte (%d). Export kaputt oder Format geändert? Zähler: %s' % (st['behalten'], dict(st)))
    rows.sort()
    day = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')
    fname = 'de-%s.tsv.gz' % day
    data = (VERSION_LINE + '\n' + '\n'.join(r[2] for r in rows) + '\n').encode('utf-8')
    gz = gzip.compress(data, compresslevel=9, mtime=0)
    with open(os.path.join(out, fname), 'wb') as fh:
        fh.write(gz)
    v = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
    man = {'format': 'tb1', 'v': v, 'file': fname, 'n': len(rows), 'bytes': len(gz), 'raw': len(data),
           'sha256': hashlib.sha256(gz).hexdigest(), 'quelle': 'Open Food Facts (https://world.openfoodfacts.org), ODbL 1.0'}
    with open(os.path.join(out, 'manifest.json'), 'w', encoding='utf-8') as fh:
        json.dump(man, fh, ensure_ascii=False, indent=1)
    ret = {}
    for shop in RETAIL:
        ret[shop] = {'summe': shops[shop], 'marken': [[brand_from_tag(i), c] for i, c in shop_brand[shop].most_common()]}
    rep = {'stand': v, 'datei': fname, 'mb': round(len(gz) / 1e6, 1), 'mb_entpackt': round(len(data) / 1e6, 1), 'zaehler': dict(st),
           'markenspalte': brand_col, 'sekunden': round(time.time() - t0),
           'top_marken': [[brand_from_tag(i), c] for i, c in brands.most_common(80)], 'handel': ret}
    with open(os.path.join(out, 'report.json'), 'w', encoding='utf-8') as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=1)
    md = ['# Deutsche Produkte, Stand %s' % v, '',
          '- Produkte in der Datei: **%d** (%s MB gepackt, %s MB entpackt)' % (len(rows), rep['mb'], rep['mb_entpackt']),
          '- Zeilen im Export: %d, davon Deutschland: %d' % (st['zeilen'], st['deutschland']),
          '- Aussortiert: ohne Kalorien %d, ohne Name %d, ohne Barcode %d, unplausibel %d' % (
              st['ohne_kalorien'], st['ohne_name'], st['ohne_code'], st['kalorien_unplausibel'] + st['naehrwerte_unplausibel']),
          '- Markenspalte: %s, Laufzeit %d s' % (brand_col, rep['sekunden']), '',
          '## Handelsmarken (eigene Zuordnung, %d Produkte)' % st['handelsmarke'], '']
    for shop, r in ret.items():
        md.append('- **%s**: %d Produkte. %s' % (shop, r['summe'], ', '.join('%s %d' % (b, c) for b, c in r['marken'][:12])))
    md += ['', '## Häufigste Marken', '']
    md += ['%d. %s: %d' % (i + 1, b, c) for i, (b, c) in enumerate(rep['top_marken'][:60])]
    md += ['', 'Daten: Open Food Facts, Open Database License (ODbL) 1.0.', '']
    with open(os.path.join(out, 'report.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(md))
    print('\n'.join(md[:8]))


if __name__ == '__main__':
    main()
