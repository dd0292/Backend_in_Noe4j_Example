from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import uuid

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
        UsuarioInput("U005","Elena","elena@mail.com","2025-01-05")
    ]
    for u in usuarios:
        upsert_usuario(driver, u)

    print("Creando publicaciones...")
    create_publicacion(driver, "ana@mail.com", PublicacionInput(
        "Exploring Neo4j basics!", "2025-02-01", 10, ["tech","music"]))
    create_publicacion(driver, "bruno@mail.com", PublicacionInput(
        "My best pasta recipe!", "2025-02-02", 8, ["food"]))
    create_publicacion(driver, "carla@mail.com", PublicacionInput(
        "Trip to Peru", "2025-02-03", 15, ["travel"]))
    create_publicacion(driver, "diego@mail.com", PublicacionInput(
        "Soccer weekend", "2025-02-04", 4, ["sports"]))
    create_publicacion(driver, "elena@mail.com", PublicacionInput(
        "Top 10 playlists", "2025-02-05", 6, ["music"]))

    print("Creando amistades...")
    create_amistad(driver, "ana@mail.com", "bruno@mail.com")
    create_amistad(driver, "ana@mail.com", "carla@mail.com")
    create_amistad(driver, "bruno@mail.com", "diego@mail.com")

    print("Creando seguimientos...")
    create_seguimiento(driver, "elena@mail.com", "ana@mail.com")
    create_seguimiento(driver, "carla@mail.com", "diego@mail.com")

# ------------------------------------------------------------
# DEMO / MAIN
# ------------------------------------------------------------
def main():
    print(f"Conectando a Neo4j en {URI} ...")
    with get_driver() as driver:
        print("Conexión OK.")

        print("Eliminando datos previos...")
        delete_all(driver)

        print("Creando constraints...")
        init_schema(driver)

        print("Sembrando datos...")
        seed_data(driver)

        print("\nTop publicaciones:")
        for row in top_publicaciones(driver):
            print(publicacion_to_str(row))

        print("\nPublicaciones de Ana:")
        for row in publicaciones_por_usuario(driver, "ana@mail.com"):
            print(publicacion_to_str(row))

        print("\nAmigos en común entre Ana y Bruno:")
        print(amigos_en_comun(driver, "ana@mail.com", "bruno@mail.com"))

        print("\nSugerencias de amigos para Ana:")
        print(sugerencias_de_amigos(driver, "ana@mail.com"))

        print("\n Amigos en común entre Carla y Bruno (sin amistad directa):")
        print(amigos_en_comun(driver, "carla@mail.com", "bruno@mail.com"))

        print("\nListo.")

if __name__ == "__main__":
    main()
