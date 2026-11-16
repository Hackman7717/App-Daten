/* Welche Muskeln eine Übung trainiert – für das 3D-Modell aus Z-Anatomy (CC BY-SA 4.0).
   MUS: Muskelgruppen der App (id → Name, Knoten im Modell ohne .l/.r).
   EX_MUS: je Standardübung (id aus EX_LIB) Hauptmuskeln p und mitarbeitende Muskeln s.
   FAM_MUS: dasselbe je Übungsname (gilt für alle Varianten, wenn die id nicht eigens steht).
   SUB_MUS: Rückfall für eigene Übungen über ihre Muskelgruppe bzw. Kategorie. */
var MUS = {
  brust:        ['Großer Brustmuskel', ['Sternocostal head of pectoralis major muscle', '(Abdominal part of pectoralis major muscle)']],
  brust_oben:   ['Oberer Brustmuskel', ['Clavicular head of pectoralis major muscle']],
  serratus:     ['Sägemuskel', ['Serratus anterior muscle']],
  sch_vorne:    ['Vordere Schulter', ['Clavicular part of deltoid muscle']],
  sch_seite:    ['Seitliche Schulter', ['Acromial part of deltoid muscle']],
  sch_hinten:   ['Hintere Schulter', ['Scapular spinal part of deltoid muscle']],
  rotatoren:    ['Rotatorenmanschette', ['Infraspinatus muscle', 'Teres minor muscle', 'Supraspinatus muscle']],
  trapez_oben:  ['Oberer Trapezmuskel', ['Descending part of trapezius muscle', 'Levator scapulae']],
  trapez_mitte: ['Mittlerer Trapezmuskel', ['Transverse part of trapezius muscle']],
  trapez_unten: ['Unterer Trapezmuskel', ['Ascending part of trapezius muscle']],
  rhomboiden:   ['Rautenmuskeln', ['Rhomboid major muscle', 'Rhomboid minor muscle']],
  lat:          ['Latissimus', ['Latissimus dorsi muscle']],
  teres:        ['Großer Rundmuskel', ['Teres major muscle']],
  ruecken:      ['Rückenstrecker', ['Iliocostalis lumborum muscle', 'Iliocostalis thoracis muscle', 'Longissimus thoracis muscle', 'Spinalis thoracis muscle', 'Quadratus lumborum muscle']],
  bizeps:       ['Bizeps', ['Long head of biceps brachii', 'Short head of biceps brachii']],
  brachialis:   ['Oberarmmuskel (Brachialis)', ['Brachialis muscle']],
  brachiorad:   ['Oberarm-Speichen-Muskel', ['Brachioradialis muscle']],
  trizeps:      ['Trizeps', ['Long head of triceps brachii', 'Lateral head of triceps brachii', 'Medial head of triceps brachii', 'Anconeus muscle']],
  ua_beuger:    ['Unterarmbeuger', ['Flexor carpi radialis', 'Palmaris longus muscle', 'Humeral head of flexor carpi ulnaris', 'Ulnar head of flexor carpi ulnaris', 'Humero-ulnar head of flexor digitorum superficialis', 'Radial head of flexor digitorum superficialis', 'Superficial head of pronator teres', 'Deep head of pronator teres']],
  ua_strecker:  ['Unterarmstrecker', ['Extensor carpi radialis longus', 'Extensor carpi radialis brevis', 'Extensor digitorum', 'Humeral head of extensor carpi ulnaris', 'Ulnar head of extensor carpi ulnaris']],
  bauch:        ['Gerader Bauchmuskel', ['Rectus abdominis muscle']],
  bauch_schraeg:['Schräge Bauchmuskeln', ['External abdominal oblique muscle']],
  hueftbeuger:  ['Hüftbeuger', ['Psoas major', 'Iliacus muscle', 'Sartorius muscle']],
  quad:         ['Quadrizeps', ['Rectus femoris muscle', 'Vastus lateralis muscle', 'Vastus medialis muscle']],
  beinbeuger:   ['Beinbeuger', ['Long head of biceps femoris', 'Short head of biceps femoris', 'Semitendinosus muscle', 'Semimembranosus muscle']],
  po:           ['Großer Gesäßmuskel', ['Gluteus maximus muscle']],
  po_mitte:     ['Mittlerer Gesäßmuskel', ['Gluteus medius muscle', 'Tensor fasciae latae']],
  adduktoren:   ['Adduktoren', ['Adductor longus', 'Adductor brevis', 'Adductor magnus', 'Gracilis muscle', 'Pectineus muscle']],
  waden:        ['Waden (Zwillingswadenmuskel)', ['Medial head of gastrocnemius', 'Lateral head of gastrocnemius', 'Plantaris muscle']],
  soleus:       ['Schollenmuskel', ['Soleus muscle']],
  schienbein:   ['Vorderer Schienbeinmuskel', ['Tibialis anterior muscle']]
};

/* Von welcher Seite man den Muskel am besten sieht (für die automatische Drehung); fehlt = beide */
var MUS_SIDE = {brust:'v', brust_oben:'v', serratus:'v', sch_vorne:'v', bizeps:'v', brachialis:'v', brachiorad:'v', ua_beuger:'v', bauch:'v',
  bauch_schraeg:'v', hueftbeuger:'v', quad:'v', adduktoren:'v', schienbein:'v',
  sch_hinten:'h', rotatoren:'h', trapez_oben:'h', trapez_mitte:'h', trapez_unten:'h', rhomboiden:'h', lat:'h', teres:'h', ruecken:'h',
  trizeps:'h', ua_strecker:'h', beinbeuger:'h', po:'h', waden:'h', soleus:'h'};

/* Deutsche Namen für einzelne Teile, die zu keiner Gruppe gehören (beim Antippen) */
var MUS_DE = {
  'Sternocleidomastoid muscle': 'Kopfwender', 'Splenius capitis muscle': 'Riemenmuskel', 'Splenius colli muscle': 'Riemenmuskel',
  'Iliotibial tract': 'Iliotibialband', 'Calcaneal tendon': 'Achillessehne', 'Fibularis longus muscle': 'Langer Wadenbeinmuskel',
  'Fibularis brevis muscle': 'Kurzer Wadenbeinmuskel', 'Fibularis tertius muscle': 'Dritter Wadenbeinmuskel',
  'Extensor digitorum longus': 'Langer Zehenstrecker', 'Tendon of extensor digitorum longus': 'Sehne des Zehenstreckers',
  'Extensor hallucis longus': 'Langer Großzehenstrecker', '(Adductor minimus)': 'Adduktoren', 'Skelett': 'Skelett'
};

var FAM_MUS = {
  'Kniebeuge':              {p: ['quad', 'po'], s: ['adduktoren', 'ruecken', 'beinbeuger']},
  'Frontkniebeuge':         {p: ['quad'], s: ['po', 'adduktoren', 'ruecken', 'bauch']},
  'Goblet Squat':           {p: ['quad', 'po'], s: ['adduktoren', 'bauch']},
  'Bulgarian Split Squat':  {p: ['quad', 'po'], s: ['adduktoren', 'beinbeuger', 'po_mitte']},
  'Ausfallschritte':        {p: ['quad', 'po'], s: ['adduktoren', 'beinbeuger', 'po_mitte']},
  'Beinpresse':             {p: ['quad', 'po'], s: ['adduktoren']},
  'Hackenschmidt':          {p: ['quad'], s: ['po', 'adduktoren']},
  'Beinstrecker':           {p: ['quad'], s: []},
  'Rumänisches Kreuzheben': {p: ['beinbeuger', 'po'], s: ['ruecken', 'adduktoren', 'ua_beuger']},
  'Beinbeuger':             {p: ['beinbeuger'], s: ['waden']},
  'Hip Thrust':             {p: ['po'], s: ['beinbeuger', 'quad', 'po_mitte']},
  'Beckenheben':            {p: ['po'], s: ['beinbeuger']},
  'Glute Kickbacks':        {p: ['po'], s: ['beinbeuger']},
  'Abduktoren':             {p: ['po_mitte'], s: ['po']},
  'Kettlebell Swings':      {p: ['po', 'beinbeuger'], s: ['ruecken', 'sch_vorne', 'bauch', 'ua_beuger']},
  'Wadenheben':             {p: ['waden'], s: ['soleus']},
  'Adduktoren':             {p: ['adduktoren'], s: []},
  'Bankdrücken':            {p: ['brust'], s: ['brust_oben', 'sch_vorne', 'trizeps']},
  'Schrägbankdrücken':      {p: ['brust_oben', 'sch_vorne'], s: ['brust', 'trizeps']},
  'Brustpresse':            {p: ['brust'], s: ['brust_oben', 'sch_vorne', 'trizeps']},
  'Butterfly':              {p: ['brust'], s: ['brust_oben', 'sch_vorne']},
  'Fliegende':              {p: ['brust'], s: ['brust_oben', 'sch_vorne']},
  'Liegestütze':            {p: ['brust'], s: ['trizeps', 'sch_vorne', 'bauch', 'serratus']},
  'Dips':                   {p: ['brust', 'trizeps'], s: ['sch_vorne']},
  'Klimmzüge':              {p: ['lat'], s: ['teres', 'bizeps', 'brachialis', 'rhomboiden', 'trapez_unten', 'sch_hinten']},
  'Latzug':                 {p: ['lat'], s: ['teres', 'bizeps', 'brachialis', 'rhomboiden', 'trapez_unten']},
  'Überzüge':               {p: ['lat'], s: ['teres', 'brust', 'trizeps', 'serratus']},
  'Rudern':                 {p: ['lat', 'rhomboiden', 'trapez_mitte'], s: ['sch_hinten', 'teres', 'bizeps', 'brachialis']},
  'Reverse Butterfly':      {p: ['sch_hinten'], s: ['rhomboiden', 'trapez_mitte', 'rotatoren']},
  'Shrugs':                 {p: ['trapez_oben'], s: ['ua_beuger']},
  'Kreuzheben':             {p: ['po', 'beinbeuger', 'ruecken'], s: ['quad', 'lat', 'trapez_oben', 'adduktoren', 'ua_beuger']},
  'Rückenstrecker':         {p: ['ruecken'], s: ['po', 'beinbeuger']},
  'Schulterdrücken':        {p: ['sch_vorne', 'sch_seite'], s: ['trizeps', 'trapez_oben', 'brust_oben', 'serratus']},
  'Arnold Press':           {p: ['sch_vorne', 'sch_seite'], s: ['trizeps', 'brust_oben']},
  'Frontheben':             {p: ['sch_vorne'], s: ['brust_oben', 'sch_seite']},
  'Seitheben':              {p: ['sch_seite'], s: ['trapez_oben', 'sch_vorne']},
  'Aufrechtes Rudern':      {p: ['sch_seite', 'trapez_oben'], s: ['bizeps', 'brachialis', 'sch_vorne']},
  'Face Pulls':             {p: ['sch_hinten', 'rotatoren'], s: ['trapez_mitte', 'rhomboiden']},
  'Bizeps-Curl':            {p: ['bizeps'], s: ['brachialis', 'brachiorad', 'ua_beuger']},
  'Hammer-Curl':            {p: ['brachialis', 'brachiorad'], s: ['bizeps']},
  'Konzentrationscurl':     {p: ['bizeps'], s: ['brachialis']},
  'Scott-Curl':             {p: ['bizeps', 'brachialis'], s: ['brachiorad']},
  'Trizepsdrücken':         {p: ['trizeps'], s: []},
  'French Press':           {p: ['trizeps'], s: []},
  'Trizepsstrecken über Kopf': {p: ['trizeps'], s: []},
  'Trizeps-Kickbacks':      {p: ['trizeps'], s: ['sch_hinten']},
  'Enges Bankdrücken':      {p: ['trizeps', 'brust'], s: ['sch_vorne', 'brust_oben']},
  'Trizepsmaschine':        {p: ['trizeps'], s: []},
  'Bankdips':               {p: ['trizeps'], s: ['brust', 'sch_vorne']},
  'Handgelenk-Curl':        {p: ['ua_beuger'], s: []},
  'Reverse-Curl':           {p: ['brachiorad', 'ua_strecker'], s: ['brachialis', 'bizeps']},
  'Unterarmstütz':          {p: ['bauch'], s: ['bauch_schraeg', 'sch_vorne', 'po', 'quad', 'serratus']},
  'Seitstütz':              {p: ['bauch_schraeg'], s: ['po_mitte', 'bauch', 'sch_seite']},
  'Crunches':               {p: ['bauch'], s: ['bauch_schraeg']},
  'Sit-ups':                {p: ['bauch', 'hueftbeuger'], s: ['bauch_schraeg']},
  'Beinheben':              {p: ['bauch', 'hueftbeuger'], s: ['bauch_schraeg']},
  'Russian Twist':          {p: ['bauch_schraeg'], s: ['bauch', 'hueftbeuger']},
  'Bauchroller':            {p: ['bauch'], s: ['lat', 'bauch_schraeg', 'sch_vorne', 'serratus', 'trizeps']},
  'Holzhacker':             {p: ['bauch_schraeg'], s: ['bauch', 'sch_vorne']},
  'Laufen':                 {p: ['quad', 'beinbeuger', 'waden', 'po'], s: ['soleus', 'hueftbeuger', 'schienbein']},
  'Laufband':               {p: ['quad', 'beinbeuger', 'waden', 'po'], s: ['soleus', 'hueftbeuger', 'schienbein']},
  'Gehen':                  {p: ['po', 'waden'], s: ['quad', 'beinbeuger', 'soleus', 'schienbein']},
  'Radfahren':              {p: ['quad', 'po'], s: ['beinbeuger', 'waden', 'soleus']},
  'Fahrradergometer':       {p: ['quad', 'po'], s: ['beinbeuger', 'waden', 'soleus']},
  'Crosstrainer':           {p: ['quad', 'po'], s: ['beinbeuger', 'waden', 'brust', 'lat', 'trizeps']},
  'Treppensteiger':         {p: ['quad', 'po'], s: ['beinbeuger', 'waden', 'soleus']},
  'Rudergerät':             {p: ['quad', 'lat', 'po'], s: ['rhomboiden', 'trapez_mitte', 'beinbeuger', 'bizeps', 'sch_hinten', 'ruecken']},
  'Schwimmen':              {p: ['lat', 'sch_vorne', 'sch_seite'], s: ['brust', 'trizeps', 'bauch', 'quad']},
  'Seilspringen':           {p: ['waden', 'soleus'], s: ['quad', 'sch_seite', 'ua_beuger']},
  'Burpees':                {p: ['quad', 'brust'], s: ['po', 'trizeps', 'sch_vorne', 'bauch', 'waden']},
  'Hampelmann':             {p: ['waden', 'sch_seite'], s: ['po_mitte', 'adduktoren', 'quad']},
  'Mountain Climbers':      {p: ['bauch', 'hueftbeuger'], s: ['sch_vorne', 'quad', 'bauch_schraeg']},
  'Battle Ropes':           {p: ['sch_vorne', 'sch_seite'], s: ['bauch', 'ua_beuger', 'bizeps', 'trizeps']}
};

/* Varianten, bei denen sich die Muskeln deutlich unterscheiden (id aus EX_LIB) */
var EX_MUS = {
  'k-kzug':  {p: ['lat', 'bizeps'], s: ['teres', 'brachialis', 'rhomboiden', 'trapez_unten']},          // Klimmzüge Untergriff
  'k-latu':  {p: ['lat', 'bizeps'], s: ['teres', 'brachialis', 'rhomboiden']},                          // Latzug Untergriff
  'k-late':  {p: ['lat'], s: ['teres', 'bizeps', 'brachialis', 'rhomboiden', 'trapez_mitte']},          // Latzug enger Griff
  'k-rulh':  {p: ['lat', 'rhomboiden', 'trapez_mitte'], s: ['sch_hinten', 'teres', 'bizeps', 'ruecken', 'beinbeuger']}, // Rudern Langhantel (vorgebeugt)
  'k-tbar':  {p: ['lat', 'rhomboiden', 'trapez_mitte'], s: ['sch_hinten', 'teres', 'bizeps', 'ruecken']},
  'k-khsu':  {p: ['po', 'adduktoren', 'quad'], s: ['beinbeuger', 'ruecken', 'trapez_oben', 'ua_beuger']}, // Kreuzheben Sumo
  'k-wads':  {p: ['soleus'], s: ['waden']},                                                           // Wadenheben sitzend
  'k-bdkh':  {p: ['brust'], s: ['brust_oben', 'sch_vorne', 'trizeps']},
  'k-hbh':   {p: ['bauch', 'hueftbeuger'], s: ['bauch_schraeg', 'lat', 'ua_beuger']},                // Beinheben hängend
  'k-dipm':  {p: ['trizeps', 'brust'], s: ['sch_vorne']},
  'k-crk':   {p: ['bauch'], s: ['bauch_schraeg', 'lat']}
};

var SUB_MUS = {
  'Quadrizeps': ['quad'], 'Beinbeuger': ['beinbeuger'], 'Po': ['po'], 'Waden': ['waden', 'soleus'], 'Adduktoren': ['adduktoren'],
  'Latissimus': ['lat'], 'Oberer Rücken': ['trapez_mitte', 'rhomboiden'], 'Unterer Rücken': ['ruecken'],
  'Vorne': ['sch_vorne'], 'Seitlich': ['sch_seite'], 'Hinten': ['sch_hinten'],
  'Bizeps': ['bizeps'], 'Trizeps': ['trizeps'], 'Unterarme': ['ua_beuger', 'ua_strecker'],
  'Beine': ['quad', 'beinbeuger', 'po'], 'Brust': ['brust', 'brust_oben'], 'Rücken': ['lat', 'trapez_mitte', 'rhomboiden'],
  'Schultern': ['sch_vorne', 'sch_seite', 'sch_hinten'], 'Arme': ['bizeps', 'trizeps'],
  'Bauch & Core': ['bauch', 'bauch_schraeg'], 'Ausdauer': []
};

/* Muskeln einer Übung: e = Eintrag aus S.exercises bzw. EX_LIB-Zeile {id, name, cat, sub} */
function exMuscles(e) {
  if (e.mus) return e.mus;                       // später: selbst gewählt
  if (EX_MUS[e.id]) return EX_MUS[e.id];
  var f = FAM_MUS[(e.name || '').trim()];
  if (f) return f;
  return {p: SUB_MUS[e.sub] || SUB_MUS[e.cat] || [], s: []};
}
