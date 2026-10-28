#!/usr/bin/env python3
"""Deutsche Produkte aus dem vollständigen JSONL-Export von Open Food Facts (openfoodfacts-products.jsonl.gz, etwa 13 GB gepackt).

Aufruf (gestreamt, ohne Zwischendatei):
    curl … openfoodfacts-products.jsonl.gz | gzip -dc | grep -F '"en:germany"' | python3 build_de_json.py out
Vorteile gegenüber dem CSV-Export: deutsche Namen (product_name_de), Hauptsprache (lang) für die Reihenfolge und die Werte
„wie verkauft“, wenn Open Food Facts sonst die zubereiteten nimmt.
Nährwerte (Schema seit 2026): nutrition.aggregated_set (pro 100 g/ml, Standardeinheiten); ist der zubereitet, nimmt das Skript
einen Satz „as_sold“ aus nutrition.input_sets und rechnet ihn auf 100 um. Ältere Produkte: nutriments.
Behalten wird ein Produkt mit Land „en:germany“, Name und Kalorien (0 bis 950 kcal pro 100 g/ml).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from de_common import Collector, clean, de_pop, num, rank_score, unit_from_qty  # noqa: E402

UNIT_G = {'g': 1.0, 'mg': 1e-3, 'µg': 1e-6, 'μg': 1e-6, 'mcg': 1e-6, 'kg': 1000.0}
SRC_RANK = {'manufacturer': 0, 'packaging': 1, 'usda': 2, 'estimate': 3}


def nval(nuts, nid):
    x = nuts.get(nid) if isinstance(nuts, dict) else None
    if not isinstance(x, dict):
        return None, ''
    v = num(x.get('value'))
    if v is None:
        v = num(x.get('value_computed'))
    return v, str(x.get('unit') or '').strip().lower()


def energy_kcal(nuts):
    v, u = nval(nuts, 'energy-kcal')
    if v is not None:
        return v / 4.184 if u == 'kj' else v
    for nid in ('energy-kj', 'energy'):
        v, u = nval(nuts, nid)
        if v is not None:
            return v if u == 'kcal' else v / 4.184
    return None


def macro(nuts, nid):
    v, u = nval(nuts, nid)
    if v is None:
        return None
    return v * UNIT_G.get(u or 'g', 1.0)


def per100(s):
    """Faktor, um einen Nährwertsatz auf 100 g/ml umzurechnen (None, wenn das nicht geht)."""
    per = s.get('per')
    if per in ('100g', '100ml'):
        return 1.0
    q = num(s.get('per_quantity'))
    u = str(s.get('per_unit') or '').lower()
    f = {'g': 1, 'ml': 1, 'kg': 1000, 'l': 1000, 'cl': 10, 'dl': 100}.get(u)
    if not q or not f or q * f < 5:
        return None
    return 100.0 / (q * f)


def set_unit(s):
    per, u = s.get('per'), str(s.get('per_unit') or '').lower()
    if per == '100ml' or u in ('ml', 'l', 'cl', 'dl'):
        return 'ml'
    if per == '100g' or u in ('g', 'kg'):
        return 'g'
    return None


def nutrition(d, st):
    nu = d.get('nutrition') if isinstance(d.get('nutrition'), dict) else {}
    agg = nu.get('aggregated_set') if isinstance(nu.get('aggregated_set'), dict) else None
    sets = [s for s in (nu.get('input_sets') or []) if isinstance(s, dict)] if isinstance(nu.get('input_sets'), list) else []
    if agg and agg.get('preparation') == 'prepared':
        cands = [s for s in sets if s.get('preparation') == 'as_sold' and per100(s) and isinstance(s.get('nutrients'), dict)]
        cands.sort(key=lambda s: (SRC_RANK.get(s.get('source'), 4), 0 if s.get('per') in ('100g', '100ml') else 1))
        for s in cands:
            k = energy_kcal(s['nutrients'])
            if k is None:
                continue
            f = per100(s)
            mac = [macro(s['nutrients'], x) for x in ('proteins', 'carbohydrates', 'fat')]
            st['werte_wie_verkauft'] += 1
            return k * f, [None if m is None else m * f for m in mac], set_unit(s)
    if agg and isinstance(agg.get('nutrients'), dict):
        n = agg['nutrients']
        k = energy_kcal(n)
        if k is not None:
            st['werte_' + str(agg.get('preparation') or 'ohne_angabe')] += 1
            return k, [macro(n, x) for x in ('proteins', 'carbohydrates', 'fat')], {'100ml': 'ml', '100g': 'g'}.get(agg.get('per'))
    nm = d.get('nutriments') if isinstance(d.get('nutriments'), dict) else {}
    if nm:
        k = num(nm.get('energy-kcal_100g'))
        if k is None:
            kj = num(nm.get('energy-kj_100g'))
            kj = kj if kj is not None else num(nm.get('energy_100g'))
            k = kj / 4.184 if kj is not None else None
        if k is not None:
            st['werte_alt'] += 1
            return k, [num(nm.get(x)) for x in ('proteins_100g', 'carbohydrates_100g', 'fat_100g')], None
    return None, [None, None, None], None


def pick_name(d):
    """Deutscher Name zuerst, dann der Name in der Hauptsprache, wenn die Deutsch ist, dann Englisch, dann irgendeiner."""
    v = clean(d.get('product_name_de'), 80)
    if v:
        return v, True
    if d.get('lang') == 'de':
        v = clean(d.get('product_name'), 80)
        if v:
            return v, True
    for k in ('product_name_en', 'product_name', 'generic_name_de', 'generic_name'):
        v = clean(d.get(k), 80)
        if v:
            return v, k.endswith('_de')
    return '', False


def front_img(d):
    im = d.get('images')
    if not isinstance(im, dict):
        return ''
    langs = ['de', str(d.get('lang') or ''), 'en']
    sel = im.get('selected')
    if isinstance(sel, dict):
        fr = sel.get('front')
        if isinstance(fr, dict):
            for lg in langs + sorted(fr.keys()):
                x = fr.get(lg)
                if isinstance(x, dict) and str(x.get('rev') or '').strip():
                    return 'front_%s.%s.200' % (lg, str(x['rev']).strip())
        return ''
    for lg in langs + sorted(k[6:] for k in im if k.startswith('front_')):
        x = im.get('front_' + lg)
        if isinstance(x, dict) and str(x.get('rev') or '').strip():
            return 'front_%s.%s.200' % (lg, str(x['rev']).strip())
    return ''


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'out'
    C = Collector('JSONL-Export (openfoodfacts-products.jsonl.gz)')
    st = C.st
    for raw in sys.stdin.buffer:
        st['gelesen'] += 1
        try:
            d = json.loads(raw)
        except ValueError:
            st['json_fehler'] += 1
            continue
        if not isinstance(d, dict) or 'en:germany' not in (d.get('countries_tags') or []):
            continue
        if d.get('obsolete') in (True, 'on', 1, '1'):
            st['veraltet'] += 1
            continue
        st['deutschland'] += 1
        name, name_de = pick_name(d)
        if name:
            st['name_de' if name_de else 'name_andere'] += 1
        k, mac, unit = nutrition(d, st)
        qty = clean(d.get('quantity'), 30)
        brands = d.get('brands')
        brand = clean((brands if isinstance(brands, str) else ','.join(map(str, brands or []))).split(',')[0], 40)
        btags = [str(t) for t in (d.get('brands_tags') or []) if t]
        best, least, topc = de_pop(d.get('popularity_tags'))
        score = rank_score(best, least, topc, d.get('lang') == 'de', name_de, num(d.get('unique_scans_n')) or 0)
        # Getränke in ml, auch wenn Open Food Facts die Werte pro 100 g führt (Milch steht oft so drin)
        unit = 'ml' if unit == 'ml' or unit_from_qty(qty) == 'ml' else 'g'
        C.add(str(d.get('code') or ''), name, brand, btags, qty, unit, k, mac, num(d.get('serving_quantity')),
              front_img(d), score)
    C.write(out)


if __name__ == '__main__':
    main()
