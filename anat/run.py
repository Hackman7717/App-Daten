# Kurzprüfung: Gibt es Haut / Körperoberfläche im Modell?
import bpy, sys, os, re
out = sys.argv[sys.argv.index('--') + 1]; os.makedirs(out, exist_ok=True)
L = []
for c in bpy.data.collections:
    if re.search(r'skin|integument|cutis|surface|body|outline|silhou', c.name, re.I):
        ms = [o for o in c.all_objects if o.type == 'MESH']
        L.append('COL %s  meshes=%d verts=%d' % (c.name, len(ms), sum(len(o.data.vertices) for o in ms)))
for o in bpy.data.objects:
    if o.type == 'MESH' and re.search(r'skin|integument|cutis|body surface|epiderm', o.name, re.I):
        L.append('OBJ %s v=%d cols=%s' % (o.name, len(o.data.vertices), [c.name for c in o.users_collection]))
top = [c.name for c in bpy.context.scene.collection.children]
L.append('TOP ' + ' | '.join(top))
for c in bpy.context.scene.collection.children:
    L.append('  ' + c.name + ' -> ' + ' | '.join(k.name for k in c.children))
open(os.path.join(out, 'haut.txt'), 'w').write('\n'.join(L)); print('\n'.join(L))
