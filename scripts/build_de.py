#!/usr/bin/env python3
"""Deutsche Produkte aus dem CSV-Export von Open Food Facts (Rückfall, falls der JSONL-Export nicht klappt).

Aufruf: curl … en.openfoodfacts.org.products.csv.gz | gunzip -c | python3 build_de.py out
Der CSV-Export ist die englische Fassung: Namen kommen dort bevorzugt auf Englisch (product_name_en), Marken teils nur als Kennung.
Behalten wird ein Produkt mit Land „en:germany“, Name und Kalorien (0 bis 950 kcal pro 100 g/ml).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from de_common import Collector, brand_from_tag, clean, de_pop, img_key, num, rank_score, unit_from_qty  # noqa: E402


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'out'
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
    i_ctry, _ = col('countries_tags', 'countries', need=True)
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
    i_pop, _ = col('popularity_tags')
    i_img, _ = col('image_small_url', 'image_front_small_url')
    need = max(i for i in [i_code, i_name, i_ctry] if i is not None)

    C = Collector('CSV-Export (en.openfoodfacts.org.products.csv.gz)')
    st = C.st
    for raw in inp:
        st['gelesen'] += 1
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
        code = g(i_code)
        name = clean(g(i_name), 80) or clean(g(i_gen), 80)
        k = num(g(i_kcal))
        if k is None:
            kj = num(g(i_kj))
            if kj is None:
                kj = num(g(i_en))
            k = kj / 4.184 if kj is not None else None
        mac = [num(g(i)) for i in (i_p, i_c, i_f)]
        btags = [t for t in g(i_btags).split(',') if t.strip()] if i_btags is not None else []
        brand = clean(g(i_brand).split(',')[0], 40) if brand_col == 'brands' else (brand_from_tag(btags[0]) if btags else '')
        qty = clean(g(i_qty), 30)
        best, least, topc = de_pop(g(i_pop).split(','))
        score = rank_score(best, least, topc, False, False, num(g(i_scan)) or 0)
        C.add(code, name, brand, btags, qty, unit_from_qty(qty), k, mac, num(g(i_svq)), img_key(code, g(i_img)), score)
    C.write(out, {'markenspalte': brand_col})


if __name__ == '__main__':
    main()
