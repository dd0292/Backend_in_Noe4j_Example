# database.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import uuid
import random
from datetime import datetime, timedelta


# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

load_dotenv()
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH_USER = os.getenv("NEO4J_USERNAME", "neo4j")
AUTH_PASS = os.getenv("NEO4J_PASSWORD")

# ------------------------------------------------------------
# DATA MODELS
# ------------------------------------------------------------
@dataclass
class PublicacionInput:
    contenido: str
    fecha: str
    likes: int
    etiquetas: List[str]

@dataclass
class UsuarioInput:
    id: str
    nombre: str
    email: str
    fechaRegistro: str

# ------------------------------------------------------------
# DRIVER
# ------------------------------------------------------------
def get_driver():
    driver = GraphDatabase.driver(URI, auth=(AUTH_USER, AUTH_PASS))
    driver.verify_connectivity()
    return driver

# ------------------------------------------------------------
# SCHEMA / CONSTRAINTS
# ------------------------------------------------------------
def init_schema(driver):
    schema_queries = [
        """
        CREATE CONSTRAINT IF NOT EXISTS
        FOR (u:Usuario) REQUIRE u.email IS UNIQUE
        """,
        """
        CREATE CONSTRAINT IF NOT EXISTS
        FOR (u:Usuario) REQUIRE (u.id) IS NOT NULL
        """,
        """
        CREATE CONSTRAINT IF NOT EXISTS
        FOR (p:Publicación) REQUIRE p.id IS UNIQUE
        """,
        """
        CREATE CONSTRAINT IF NOT EXISTS
        FOR (e:Etiqueta) REQUIRE e.nombre IS UNIQUE
        """
    ]
    with driver.session() as s:
        for q in schema_queries:
            s.run(q)

# ------------------------------------------------------------
# CRUD / UPSERTS
# ------------------------------------------------------------
def upsert_usuario(driver, user: UsuarioInput):
    q = """
    MERGE (u:Usuario {email:$email})
    SET u.id=$id, u.nombre=$nombre, u.fechaRegistro=date($fechaRegistro)
    RETURN u
    """
    with driver.session() as s:
        return s.run(q, **user.__dict__).single()

def insert_usuario(driver, user: UsuarioInput):
    q = """
    CREATE (u:Usuario {
        id:$id, nombre:$nombre, email:$email,
        fechaRegistro:date($fechaRegistro), Activo:1
    })
    RETURN u
    """
    with driver.session() as s:
        return s.run(q, **user.__dict__).single()

def create_publicacion(driver, user_email: str, pub: PublicacionInput):
    """
    Crea una publicación y la conecta con el autor y sus etiquetas.
    """
    def _tx(tx):
        post_id = str(uuid.uuid4())
        tx.run(
            """
            MATCH (u:Usuario {email:$email})
            MERGE (p:Publicación {id:$id})
            SET p.contenido=$contenido, p.fecha=date($fecha), p.likes=$likes
            MERGE (u)-[:CREA]->(p)
            WITH p, $etiquetas AS tags
            UNWIND tags AS tag
            MERGE (e:Etiqueta {nombre:tag})
            MERGE (p)-[:TIENE_ETIQUETA]->(e)
            """,
            email=user_email, id=post_id,
            contenido=pub.contenido, fecha=pub.fecha,
            likes=pub.likes, etiquetas=pub.etiquetas
        )
    with driver.session() as s:
        s.execute_write(_tx)

def create_amistad(driver, email_a: str, email_b: str):
    """
    Crea amistad bidireccional.
    """
    q = """
    MATCH (a:Usuario {email:$a})
    MATCH (b:Usuario {email:$b})
    MERGE (a)-[:AMIGO_DE]->(b)
    MERGE (b)-[:AMIGO_DE]->(a)
    """
    with driver.session() as s:
        s.run(q, a=email_a, b=email_b)

def create_seguimiento(driver, seguidor: str, seguido: str):
    """
    Crea relación de seguimiento unidireccional.
    """
    q = """
    MATCH (a:Usuario {email:$seguidor})
    MATCH (b:Usuario {email:$seguido})
    MERGE (a)-[:SIGUE]->(b)
    """
    with driver.session() as s:
        s.run(q, seguidor=seguidor, seguido=seguido)

def find_usuario(driver, email: str) -> Optional[Dict[str, Any]]:
    q = "MATCH (u:Usuario {email:$email}) RETURN u"
    with driver.session() as s:
        record = s.run(q, email=email).single()
        return record["u"] if record else None

# ------------------------------------------------------------
# TOSTRING
# ------------------------------------------------------------
def usuario_to_str(user: Dict[str, Any]) -> str:
    return f"{user['id']}, {user['nombre']}, {user['email']}, {user['fechaRegistro']}"

def publicacion_to_str(pub: Dict[str, Any]) -> str:
    etiquetas = ", ".join(pub.get("etiquetas", []))
    return (f"ID: {pub['id']}, Contenido: {pub['contenido']}, \nFecha: {pub['fecha']}, "
            f"Likes: {pub['likes']}, Etiquetas: [{etiquetas}]"
            + "\n" + "-"*50 + "\n")

# ------------------------------------------------------------
# QUERIES
# ------------------------------------------------------------
def publicaciones_por_usuario(driver, email: str) -> List[Dict[str, Any]]:
    q = """
    MATCH (u:Usuario {email: $email})-[:CREA]->(p:Publicación)
    OPTIONAL MATCH (p)-[:TIENE_ETIQUETA]->(e:Etiqueta)
    WITH p, collect(DISTINCT e.nombre) AS etiquetas
    RETURN p.id AS id,
           p.contenido AS contenido,
           p.fecha AS fecha,
           p.likes AS likes,
           etiquetas
    ORDER BY p.fecha DESC
    """
    with driver.session() as s:
        return [r.data() for r in s.run(q, email=email)]

def amigos_en_comun(driver, email1: str, email2: str) -> List[str]:
    q = """
    MATCH (u1:Usuario {email: $email1}), (u2:Usuario {email: $email2})
    MATCH (amigo:Usuario)
    WHERE (u1)-[:AMIGO_DE]-(amigo)
      AND (u2)-[:AMIGO_DE]-(amigo)
      AND amigo <> u1
      AND amigo <> u2
    RETURN DISTINCT coalesce(amigo.nombre, amigo.email) AS nombre
    ORDER BY nombre
    """
    with driver.session() as s:
        return [r["nombre"] for r in s.run(q, email1=email1, email2=email2)]

def top_publicaciones(driver, limit: int = 5) -> List[Dict[str, Any]]:
    q = """
    MATCH (p:Publicación)<-[:CREA]-(u:Usuario)
    OPTIONAL MATCH (p)-[:TIENE_ETIQUETA]->(e:Etiqueta)
    WITH p, u, collect(DISTINCT e.nombre) AS etiquetas
    RETURN p.id AS id,
           u.nombre AS autor,
           p.contenido AS contenido,
           p.likes AS likes,
           p.fecha AS fecha,
           etiquetas
    ORDER BY p.likes DESC
    LIMIT $limit
    """
    with driver.session() as s:
        return [r.data() for r in s.run(q, limit=limit)]

def sugerencias_de_amigos(driver, email: str) -> List[str]:
    q = """
    MATCH (u:Usuario {email: $email})-[:AMIGO_DE]-(a)-[:AMIGO_DE]-(sugerencia:Usuario)
    WHERE NOT (u)-[:AMIGO_DE]-(sugerencia)
      AND u <> sugerencia
    RETURN DISTINCT sugerencia.nombre AS nombre
    """
    with driver.session() as s:
        return [r["nombre"] for r in s.run(q, email=email)]

def get_all_usuarios(driver) -> List[Dict[str, Any]]:
    q = "MATCH (u:Usuario) RETURN u"
    with driver.session() as s:
        return [r["u"] for r in s.run(q)]
    
# ------------------------------------------------------------
# DELETES ALL
# ------------------------------------------------------------
def delete_all(driver):
    with driver.session() as s:
        s.run("MATCH (n) DETACH DELETE n")

# ------------------------------------------------------------
# EXAMPLE DATA LOAD
# ------------------------------------------------------------
def seed_data(driver):
    print("Creando usuarios...")
    usuarios = [
        UsuarioInput("U001","Ana","ana@mail.com","2025-01-01"),
        UsuarioInput("U002","Bruno","bruno@mail.com","2025-01-02"),
        UsuarioInput("U003","Carla","carla@mail.com","2025-01-03"),
        UsuarioInput("U004","Diego","diego@mail.com","2025-01-04"),
        UsuarioInput("U005","Elena","elena@mail.com","2025-01-05"),
        UsuarioInput("U006", "Fernando", "fernando@mail.com", "2024-03-01"),
        UsuarioInput("U007", "Gabriela", "gabriela@mail.com", "2024-03-05"),
        UsuarioInput("U008", "Héctor", "hector@mail.com", "2024-03-10"),
        UsuarioInput("U009", "Isabel", "isabel@mail.com", "2024-03-15"),
        UsuarioInput("U010", "Javier", "javier@mail.com", "2024-03-20"),
        UsuarioInput("U011", "Karen", "karen@mail.com", "2024-04-01"),
        UsuarioInput("U012", "Luis", "luis@mail.com", "2024-04-05"),
        UsuarioInput("U013", "María", "maria@mail.com", "2024-04-10"),
        UsuarioInput("U014", "Nicolás", "nicolas@mail.com", "2024-04-15"),
        UsuarioInput("U015", "Olivia", "olivia@mail.com", "2024-04-20")
    ]
    for u in usuarios:
        upsert_usuario(driver, u)

    print("Usando las 5 etiquetas existentes: music, travel, sports, food, tech")
    etiquetas_unicas = ["music", "travel", "sports", "food", "tech"]

    contenidos_publicaciones = [
        # Tech
        "Acabo de terminar mi primer proyecto en Neo4j, ¡es increíble! #tech",
        "Explorando las nuevas features de Python 3.12 #tech",
        "Machine Learning aplicado a datos reales #tech",
        # Music
        "Recomendaciones de música para el fin de semana? #music",
        "Concierto increíble anoche, la banda estuvo espectacular #music",
        "Mi nueva playlist para trabajar concentrado #music",
        # Travel
        "Viajando a la playa este fin de semana #travel",
        "Visitando museos en la ciudad, arte impresionante #travel",
        "Fotos increíbles de mi viaje a las montañas #travel",
        # Food
        "Receta secreta de lasaña que aprendí de mi abuela #food",
        "Preparando pizza casera desde cero #food",
        "Postre fácil y rápido: flan de chocolate #food",
        # Sports
        "Corrí mi primera maratón hoy, ¡qué experiencia! #sports",
        "Entrenamiento intensivo para el próximo torneo #sports",
        "Ganamos el partido de fútbol hoy #sports",
    ]
    
    # Crear 3 publicaciones por cada usuario
    for i, usuario in enumerate(usuarios):
        for j in range(3):
            contenido_idx = (i * 3 + j) % len(contenidos_publicaciones)
            
            dias_atras = random.randint(1, 365)
            fecha = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
            
            likes = random.randint(0, 50)
            
            num_etiquetas = random.randint(2, 3)
            etiquetas = random.sample(etiquetas_unicas, num_etiquetas)
            
            publicacion = PublicacionInput(
                contenido=contenidos_publicaciones[contenido_idx],
                fecha=fecha,
                likes=likes,
                etiquetas=etiquetas
            )
            create_publicacion(driver, usuario.email, publicacion)

    print("Creando amistades (2-3 amigos por usuario)...")
    
    emails_usuarios = [usuario.email for usuario in usuarios]
    
    for usuario_email in emails_usuarios:
        posibles_amigos = [email for email in emails_usuarios if email != usuario_email]
        num_amigos = random.randint(2, 3)
        amigos_seleccionados = random.sample(posibles_amigos, num_amigos)
        
        for amigo_email in amigos_seleccionados:
            try:
                create_amistad(driver, usuario_email, amigo_email)
            except Exception as e:
                print(f"Error creando amistad entre {usuario_email} y {amigo_email}: {e}")

    print("Población de datos completada!")
    print(f"- {len(usuarios)} usuarios creados")
    print(f"- {len(usuarios) * 3} publicaciones creadas")
    print(f"- {len(etiquetas_unicas)} etiquetas únicas")
    print("- Amistades configuradas")

# ------------------------------------------------------------
# DATABASE INFO
# ------------------------------------------------------------
def get_database_info(driver):
    """Obtiene información de la base de datos para verificación"""
    info = {}
    
    with driver.session() as s:
        # Contar usuarios
        result = s.run("MATCH (u:Usuario) RETURN count(u) as count")
        info['usuarios'] = result.single()["count"]
        
        # Contar publicaciones
        result = s.run("MATCH (p:Publicación) RETURN count(p) as count")
        info['publicaciones'] = result.single()["count"]
        
        # Contar etiquetas
        result = s.run("MATCH (e:Etiqueta) RETURN count(e) as count")
        info['etiquetas'] = result.single()["count"]
        
        # Obtener etiquetas
        result = s.run("MATCH (e:Etiqueta) RETURN e.nombre as nombre ORDER BY nombre")
        info['lista_etiquetas'] = [record["nombre"] for record in result]
        
        # Amistades por usuario (primeros 5)
        result = s.run("""
        MATCH (u:Usuario)
        RETURN u.email as email, u.nombre as nombre, 
               size([(u)-[:AMIGO_DE]-(:Usuario) | 1]) as amigos_count
        ORDER BY amigos_count DESC
        LIMIT 5
        """)
        info['top_amistades'] = [(record["nombre"], record["amigos_count"]) for record in result]
    
    return info