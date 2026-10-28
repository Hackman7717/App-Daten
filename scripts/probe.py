#!/usr/bin/env python3
"""Einmalige Stichprobe: Wie sehen deutsche Produkte im JSONL-Export aus? (Felder für Namen, Nährwerte, Bilder, Beliebtheit)"""
import collections, json, sys
docs = []
for line in open(sys.argv[1], encoding='utf-8', errors='replace'):
    try:
        d = json.loads(line)
    except Exception:
        continue
    if 'en:germany' in (d.get('countries_tags') or []):
        docs.append(d)
keys = collections.Counter()
for d in docs:
    for k in ('product_name', 'product_name_de', 'product_name_en', 'lang', 'lc', 'brands', 'quantity', 'serving_quantity', 'popularity_tags',
              'unique_scans_n', 'nutriments', 'nutrition', 'images', 'image_front_small_url', 'obsolete'):
        if k in d and d[k] not in (None, '', [], {}):
            keys[k] += 1
    n = d.get('nutrition') or {}
    if isinstance(n, dict):
        for k in n:
            keys['nutrition.' + k] += 1
        ag = n.get('aggregated_set') or {}
        if isinstance(ag, dict):
            keys['agg.preparation=' + str(ag.get('preparation'))] += 1
            keys['agg.per=' + str(ag.get('per'))] += 1
    im = d.get('images') or {}
    if isinstance(im, dict):
        keys['images.keys:' + ','.join(sorted(im.keys())[:3])] += 1
def trim(d):
    o = {k: d.get(k) for k in ('code', 'lang', 'lc', 'product_name', 'product_name_de', 'product_name_en', 'brands', 'quantity', 'serving_quantity',
                               'unique_scans_n', 'countries_tags')}
    o['popularity_tags'] = (d.get('popularity_tags') or [])[:40]
    nm = d.get('nutriments') or {}
    o['nutriments'] = {k: v for k, v in nm.items() if any(s in k for s in ('energy', 'proteins', 'carbohydrates', 'fat')) and 'saturated' not in k}
    n = d.get('nutrition') or {}
    def ns(s):
        if not isinstance(s, dict):
            return s
        r = {k: v for k, v in s.items() if k != 'nutrients'}
        r['nutrients'] = {k: v for k, v in (s.get('nutrients') or {}).items() if k in ('energy-kcal', 'energy-kj', 'energy', 'proteins', 'carbohydrates', 'fat')}
        return r
    o['nutrition'] = {'aggregated_set': ns(n.get('aggregated_set')), 'input_sets': [ns(s) for s in (n.get('input_sets') or [])][:3]} if n else None
    im = d.get('images') or {}
    if isinstance(im, dict):
        if 'selected' in im:
            o['images'] = {'selected': {k: v for k, v in (im.get('selected') or {}).items() if k == 'front'}}
        else:
            o['images'] = {k: v for k, v in im.items() if k.startswith('front')}
    return o
withn = [d for d in docs if d.get('nutrition') or d.get('nutriments')]
ex = sorted(withn, key=lambda d: -(d.get('unique_scans_n') or 0))[:4]
out = {'kopf': open(sys.argv[2]).read(), 'deutsche_docs': len(docs), 'felder': dict(keys.most_common()), 'beispiele': [trim(d) for d in ex]}
json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:3000])
