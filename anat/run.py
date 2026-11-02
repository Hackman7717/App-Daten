# Schritt 2: Muskeln (beide Seiten) und Skelett aus Z-Anatomy als ein kleines glTF.
# Jeder Muskel bleibt ein eigener, benannter Knoten (z. B. "Gluteus maximus muscle.r"),
# das Skelett wird zu einem Knoten "Skelett" zusammengefasst.
import bpy, json, sys, os, re

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)

# Muskeln, die für Training keine Rolle spielen und verdeckt oder winzig sind
SKIP = re.compile('|'.join([
    r'^\(', 'Depressor', 'Levator labii', 'Levator anguli', 'nasolabialis', 'Nasalis', 'Orbicularis', 'Procerus',
    'Risorius', 'Zygomaticus', 'Mentalis', 'Corrugator', 'Bucinator', 'Frontalis', 'Occipitalis', 'Temporoparietalis',
    'Epicranial', 'Temporalis', 'masseter', 'pterygoid', 'tarsus', 'Inferior rectus', 'Superior rectus', 'Lateral rectus',
    'Medial rectus', 'Inferior oblique muscle', 'Superior oblique muscle', 'Trochlea', 'Common tendinous', 'palpebrae',
    'digastric', 'hyoid', 'glossus', 'pharyn', 'arytenoid', 'crico', 'thyro', 'ntercostal', 'Transversus thoracis',
    'Diaphragm', 'coccygeus', 'anal', 'Tendinous arch', 'Interspinales', 'intertransversarii', 'Rotatores',
    'Levatores', 'Multifidus', 'Semispinalis', 'capitis', 'Spinalis colli', 'Longissimus colli', 'Iliocostalis colli',
    'Longus c', 'Obturator', 'gemellus', 'Quadratus femoris', 'Piriformis', 'Lumbrical', 'nterossei', 'Opponens',
    'digiti minimi', 'pollicis brevis', 'Adductor pollicis', 'adductor pollicis', 'adductor hallucis', 'hallucis brevis',
    'Abductor hallucis', 'Flexor digitorum brevis', 'Quadratus plantae', 'Extensor digitorum brevis', 'retinacul',
    'metacarpal', 'metatarsal', 'Plantar aponeurosis', 'Transversus abdominis', 'Internal abdominal oblique',
    'Serratus posterior', 'Scalenus', 'Subclavius', 'Pyramidalis', 'Linea alba', 'Inguinal ligament',
    'patellar retinaculum', 'Popliteus', 'Tibialis posterior', 'Flexor hallucis longus', 'Flexor digitorum longus',
    'Flexor digitorum profundus', 'Flexor pollicis longus', 'Pronator quadratus', 'Supinator', 'Extensor indicis',
    'Extensor pollicis', 'Abductor pollicis longus', 'Gluteus minimus', 'Vastus intermedius', 'Subscapularis',
    'Pectoralis minor', 'Coracobrachialis',
]))

def base(n):
    return n[:-2] if n[-2:] in ('.l', '.r') else n

def under(colname):
    c = bpy.data.collections.get(colname)
    res = set()
    def walk(c):
        for o in c.objects:
            if o.type == 'MESH':
                res.add(o)
        for k in c.children:
            walk(k)
    if c:
        walk(c)
    return res

muscles = sorted([o for o in (under('Muscles') | under('Superficial muscles')) if not SKIP.search(base(o.name))], key=lambda o: o.name)
bones = sorted([o for o in under('Skeletal system') if not re.search('ooth|teeth|ossicle|Malleus|Incus|Stapes|cartilage', o.name, re.I)], key=lambda o: o.name)
print('Muskeln', len(muscles), 'Knochen', len(bones))

dg = bpy.context.evaluated_depsgraph_get()

def world_mesh(o, name):
    ev = o.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=False, depsgraph=dg)
    me.transform(o.matrix_world)
    me.name = name
    return me

new = []
info = []
for o in muscles:
    me = world_mesh(o, o.name)
    v = len(me.vertices)
    if v < 4:
        continue
    ob = bpy.data.objects.new(o.name, me)
    r = min(1.0, max(220, v * 0.22) / v)
    if r < 1:
        m = ob.modifiers.new('dec', 'DECIMATE'); m.ratio = r
    new.append(ob)
    xs = [p.co for p in me.vertices]
    c = [sum(p[i] for p in xs) / v for i in range(3)]
    info.append({'n': o.name, 'v': v, 'r': round(r, 3), 'c': [round(c[0], 3), round(c[2], 3), round(-c[1], 3)],
                 'cols': [x.name for x in o.users_collection]})

# Skelett: alle Knochen vereinfacht und zu einem Mesh zusammengefügt
import bmesh
bm = bmesh.new()
bv = 0
for o in bones:
    me = world_mesh(o, 'tmp')
    v = len(me.vertices)
    if v < 4:
        bpy.data.meshes.remove(me); continue
    tmp = bpy.data.objects.new('tmp', me)
    r = min(1.0, max(40, v * 0.07) / v)
    if r < 1:
        m = tmp.modifiers.new('dec', 'DECIMATE'); m.ratio = r
    bpy.context.scene.collection.objects.link(tmp)
    dg.update()
    me2 = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bm.from_mesh(me2)
    bv += v
    bpy.context.scene.collection.objects.unlink(tmp)
    bpy.data.objects.remove(tmp); bpy.data.meshes.remove(me); bpy.data.meshes.remove(me2)
sk = bpy.data.meshes.new('Skelett')
bm.to_mesh(sk); bm.free()
print('Skelett', bv, '->', len(sk.vertices))

# Alles Alte entfernen, nur die neuen Objekte in die Szene
keep = set(new)
for o in list(bpy.data.objects):
    if o not in keep:
        bpy.data.objects.remove(o)
sc = bpy.context.scene
for c in list(sc.collection.children):
    sc.collection.children.unlink(c)
for ob in new:
    sc.collection.objects.link(ob)
skob = bpy.data.objects.new('Skelett', sk)
sc.collection.objects.link(skob)

bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'roh.glb'), export_format='GLB', use_selection=False,
                          use_visible=False, export_apply=True, export_materials='NONE', export_texcoords=False,
                          export_normals=True, export_yup=True, export_extras=False, export_animations=False)

tv = sum(len(o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices) for o in new)
json.dump({'muskeln': info, 'skelett_v': len(sk.vertices)}, open(os.path.join(out, 'muskeln.json'), 'w'), ensure_ascii=False, indent=0)
print('Knoten', len(new) + 1, 'Muskel-Ecken nach Vereinfachung ca.', tv)
print(os.path.getsize(os.path.join(out, 'roh.glb')), 'Bytes roh.glb')
