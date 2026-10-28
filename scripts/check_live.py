#!/usr/bin/env python3
"""Prüft nach dem Veröffentlichen, ob die neue Fassung online abrufbar ist: über GitHub Pages und über raw.githubusercontent.com.
Schreibt das Ergebnis als JSON (Aufruf: check_live.py out/manifest.json out/live.json). Bricht den Lauf nie ab."""
import json, os, sys, time, urllib.request

man = json.load(open(sys.argv[1], encoding='utf-8'))
owner, repo = os.environ.get('GITHUB_REPOSITORY', 'Hackman7717/App-Daten').split('/')
bases = [('pages', 'https://%s.github.io/%s/' % (owner.lower(), repo), 480), ('raw', 'https://raw.githubusercontent.com/%s/%s/gh-pages/' % (owner, repo), 240)]
res = {'version': man['v'], 'datei': man['file']}
for name, base, wait in bases:
    end = time.time() + wait
    last = ''
    res[name] = {'ok': False, 'url': base}
    while time.time() < end:
        try:
            req = urllib.request.Request(base + 'manifest.json?t=%d' % time.time(), headers={'User-Agent': 'trainingsbuch-check', 'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(req, timeout=30) as r:
                m = json.load(r)
            last = 'manifest %s' % m.get('v')
            if m.get('file') == man['file']:
                req = urllib.request.Request(base + man['file'], headers={'User-Agent': 'trainingsbuch-check', 'Origin': 'https://hackman7717.github.io'})
                with urllib.request.urlopen(req, timeout=120) as r:
                    body = r.read()
                    cors = r.headers.get('Access-Control-Allow-Origin')
                    ctype = r.headers.get('Content-Type')
                res[name] = {'ok': len(body) == man['bytes'], 'url': base, 'bytes': len(body), 'cors': cors, 'type': ctype}
                if res[name]['ok']:
                    break
                last = 'Datei noch alt (%d Bytes)' % len(body)
        except Exception as e:  # noqa: BLE001 – jeder Fehler zählt als „noch nicht da“
            last = '%s: %s' % (type(e).__name__, e)
        time.sleep(20)
    if not res[name]['ok']:
        res[name]['letzter_stand'] = last
with open(sys.argv[2], 'w', encoding='utf-8') as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
