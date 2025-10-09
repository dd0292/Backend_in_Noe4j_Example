// ────────────────────────────────────────────────────────────────
// NODOS
// ────────────────────────────────────────────────────────────────

// ETIQUETAS (TAGS)

UNWIND ['tech','food','travel','sports','music'] AS tag
MERGE (:Etiqueta {nombre: tag});

// ────────────────────────────────────────────────────────────────
// USUARIOS (15 total)
// ────────────────────────────────────────────────────────────────

UNWIND [
  {id:'U001', nombre:'Ana', email:'ana@mail.com', fecha:'2025-01-01'},
  {id:'U002', nombre:'Bruno', email:'bruno@mail.com', fecha:'2025-01-02'},
  {id:'U003', nombre:'Carla', email:'carla@mail.com', fecha:'2025-01-03'},
  {id:'U004', nombre:'Diego', email:'diego@mail.com', fecha:'2025-01-04'},
  {id:'U005', nombre:'Elena', email:'elena@mail.com', fecha:'2025-01-05'},
  {id:'U006', nombre:'Felipe', email:'felipe@mail.com', fecha:'2025-01-06'},
  {id:'U007', nombre:'Gabriela', email:'gabriela@mail.com', fecha:'2025-01-07'},
  {id:'U008', nombre:'Hugo', email:'hugo@mail.com', fecha:'2025-01-08'},
  {id:'U009', nombre:'Irene', email:'irene@mail.com', fecha:'2025-01-09'},
  {id:'U010', nombre:'Javier', email:'javier@mail.com', fecha:'2025-01-10'},
  {id:'U011', nombre:'Karla', email:'karla@mail.com', fecha:'2025-01-11'},
  {id:'U012', nombre:'Luis', email:'luis@mail.com', fecha:'2025-01-12'},
  {id:'U013', nombre:'Monica', email:'monica@mail.com', fecha:'2025-01-13'},
  {id:'U014', nombre:'Nicolas', email:'nicolas@mail.com', fecha:'2025-01-14'},
  {id:'U015', nombre:'Olivia', email:'olivia@mail.com', fecha:'2025-01-15'}
] AS u
MERGE (user:Usuario {email: u.email})
SET user.id = u.id,
    user.nombre = u.nombre,
    user.fechaRegistro = date(u.fecha);


// ────────────────────────────────────────────────────────────────
// PUBLICACIONES (30 total)
// ────────────────────────────────────────────────────────────────

UNWIND [
  {id:'P001', author:'ana@mail.com', texto:'Exploring Neo4j basics!', fecha:'2025-02-01', likes:12, etiquetas:['tech']},
  {id:'P002', author:'bruno@mail.com', texto:'My best pasta recipe!', fecha:'2025-02-02', likes:8, etiquetas:['food']},
  {id:'P003', author:'carla@mail.com', texto:'Trip to Peru', fecha:'2025-02-03', likes:15, etiquetas:['travel']},
  {id:'P004', author:'diego@mail.com', texto:'Soccer weekend', fecha:'2025-02-04', likes:4, etiquetas:['sports']},
  {id:'P005', author:'elena@mail.com', texto:'Top 10 playlists', fecha:'2025-02-05', likes:6, etiquetas:['music']},
  {id:'P006', author:'felipe@mail.com', texto:'Learning Graph DBs', fecha:'2025-02-06', likes:9, etiquetas:['tech']},
  {id:'P007', author:'gabriela@mail.com', texto:'Baking cake tutorial', fecha:'2025-02-07', likes:5, etiquetas:['food']},
  {id:'P008', author:'hugo@mail.com', texto:'Running my first marathon', fecha:'2025-02-08', likes:13, etiquetas:['sports']},
  {id:'P009', author:'irene@mail.com', texto:'Road trip to the beach', fecha:'2025-02-09', likes:10, etiquetas:['travel']},
  {id:'P010', author:'javier@mail.com', texto:'Coding late nights', fecha:'2025-02-10', likes:7, etiquetas:['tech']},
  {id:'P011', author:'karla@mail.com', texto:'Homemade sushi', fecha:'2025-02-11', likes:6, etiquetas:['food']},
  {id:'P012', author:'luis@mail.com', texto:'My workout routine', fecha:'2025-02-12', likes:9, etiquetas:['sports']},
  {id:'P013', author:'monica@mail.com', texto:'Travel gear tips', fecha:'2025-02-13', likes:11, etiquetas:['travel']},
  {id:'P014', author:'nicolas@mail.com', texto:'Best code editor', fecha:'2025-02-14', likes:14, etiquetas:['tech']},
  {id:'P015', author:'olivia@mail.com', texto:'Concert highlights', fecha:'2025-02-15', likes:8, etiquetas:['music']},
  {id:'P016', author:'ana@mail.com', texto:'Cooking for friends', fecha:'2025-02-16', likes:5, etiquetas:['food']},
  {id:'P017', author:'bruno@mail.com', texto:'Tech meetup notes', fecha:'2025-02-17', likes:12, etiquetas:['tech']},
  {id:'P018', author:'carla@mail.com', texto:'Beach volleyball', fecha:'2025-02-18', likes:7, etiquetas:['sports']},
  {id:'P019', author:'diego@mail.com', texto:'Quick JavaScript tips', fecha:'2025-02-19', likes:10, etiquetas:['tech']},
  {id:'P020', author:'elena@mail.com', texto:'Favorite recipes', fecha:'2025-02-20', likes:9, etiquetas:['food']},
  {id:'P021', author:'felipe@mail.com', texto:'Winter travel ideas', fecha:'2025-02-21', likes:6, etiquetas:['travel']},
  {id:'P022', author:'gabriela@mail.com', texto:'Running playlist', fecha:'2025-02-22', likes:7, etiquetas:['music']},
  {id:'P023', author:'hugo@mail.com', texto:'Weekend BBQ', fecha:'2025-02-23', likes:4, etiquetas:['food']},
  {id:'P024', author:'irene@mail.com', texto:'New tech trends', fecha:'2025-02-24', likes:10, etiquetas:['tech']},
  {id:'P025', author:'javier@mail.com', texto:'Cycling adventures', fecha:'2025-02-25', likes:8, etiquetas:['sports']},
  {id:'P026', author:'karla@mail.com', texto:'DIY crafts', fecha:'2025-02-26', likes:5, etiquetas:['music']},
  {id:'P027', author:'luis@mail.com', texto:'Foodie weekend', fecha:'2025-02-27', likes:7, etiquetas:['food']},
  {id:'P028', author:'monica@mail.com', texto:'Solo travel guide', fecha:'2025-02-28', likes:13, etiquetas:['travel']},
  {id:'P029', author:'nicolas@mail.com', texto:'Running challenge', fecha:'2025-03-01', likes:6, etiquetas:['sports']},
  {id:'P030', author:'olivia@mail.com', texto:'Learning guitar', fecha:'2025-03-02', likes:11, etiquetas:['music']}
] AS p
// Create post
MERGE (post:Publicación {id:p.id})
SET post.contenido = p.texto,
    post.fecha = date(p.fecha),
    post.likes = p.likes
// Connect with author
WITH post, p
MATCH (u:Usuario {email:p.author})
MERGE (u)-[:CREA]->(post)
// Connect with tags
WITH post, p
UNWIND p.etiquetas AS tag
MERGE (e:Etiqueta {nombre:tag})
MERGE (post)-[:TIENE_ETIQUETA]->(e);


// ────────────────────────────────────────────────────────────────
// RELATIONSHIPS BETWEEN USERS
// ────────────────────────────────────────────────────────────────

// FRIENDSHIPS (bidirectional)
UNWIND [
  ['ana@mail.com','bruno@mail.com'],
  ['ana@mail.com','carla@mail.com'],
  ['bruno@mail.com','diego@mail.com'],
  ['carla@mail.com','elena@mail.com'],
  ['diego@mail.com','felipe@mail.com'],
  ['elena@mail.com','gabriela@mail.com'],
  ['felipe@mail.com','hugo@mail.com'],
  ['gabriela@mail.com','irene@mail.com'],
  ['hugo@mail.com','javier@mail.com'],
  ['irene@mail.com','karla@mail.com'],
  ['javier@mail.com','luis@mail.com'],
  ['karla@mail.com','monica@mail.com'],
  ['luis@mail.com','nicolas@mail.com'],
  ['monica@mail.com','olivia@mail.com'],
  ['nicolas@mail.com','ana@mail.com']
] AS pair
WITH pair
MATCH (a:Usuario {email:pair[0]})
MATCH (b:Usuario {email:pair[1]})
MERGE (a)-[:AMIGO_DE]->(b)
MERGE (b)-[:AMIGO_DE]->(a);


// FOLLOW RELATIONSHIPS (one-way)
UNWIND [
  ['ana@mail.com','elena@mail.com'],
  ['bruno@mail.com','felipe@mail.com'],
  ['carla@mail.com','gabriela@mail.com'],
  ['diego@mail.com','irene@mail.com'],
  ['elena@mail.com','javier@mail.com'],
  ['monica@mail.com','nicolas@mail.com'],
  ['nicolas@mail.com','hugo@mail.com']
] AS f
WITH f
MATCH (a:Usuario {email:f[0]})
MATCH (b:Usuario {email:f[1]})
MERGE (a)-[:SIGUE]->(b);