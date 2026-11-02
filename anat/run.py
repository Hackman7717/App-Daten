# Schritt 1: Bestandsaufnahme des Z-Anatomy-Modells (Sammlungen, Objekte, Größe).
import bpy, json, sys, os

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)

def tree(col, depth=0):
    objs = [o for o in col.objects]
    meshes = [o for o in objs if o.type == 'MESH']
    v = sum(len(o.data.vertices) for o in meshes)
    node = {'n': col.name, 'objs': len(objs), 'meshes': len(meshes), 'verts': v,
            'hide': bool(col.hide_viewport or col.hide_render), 'kids': [tree(c, depth + 1) for c in col.children]}
    node['vtot'] = v + sum(k['vtot'] for k in node['kids'])
    node['mtot'] = len(meshes) + sum(k['mtot'] for k in node['kids'])
    return node

root = tree(bpy.context.scene.collection)

lines = []
def pr(n, d=0):
    lines.append('%s%s  [meshes %d/%d, verts %d/%d]%s' % ('  ' * d, n['n'], n['meshes'], n['mtot'], n['verts'], n['vtot'], ' (hidden)' if n['hide'] else ''))
    if d < 6:
        for k in n['kids']:
            pr(k, d + 1)
pr(root)

objs = []
for o in bpy.data.objects:
    e = {'n': o.name, 't': o.type, 'cols': [c.name for c in o.users_collection],
         'parent': o.parent.name if o.parent else None}
    if o.type == 'MESH':
        e['v'] = len(o.data.vertices); e['f'] = len(o.data.polygons)
        e['mat'] = [m.name for m in o.data.materials if m][:3]
        e['dims'] = [round(x, 3) for x in o.dimensions]
        e['mods'] = [m.type for m in o.modifiers]
    objs.append(e)

json.dump({'tree': root, 'objects': objs}, open(os.path.join(out, 'inventar.json'), 'w'), ensure_ascii=False)
open(os.path.join(out, 'inventar.txt'), 'w').write('\n'.join(lines))
print('\n'.join(lines[:120]))
print('Objekte', len(objs), 'Meshes', sum(1 for o in objs if o['t'] == 'MESH'))
