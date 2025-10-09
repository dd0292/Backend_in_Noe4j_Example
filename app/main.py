from neo4j import GraphDatabase
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import os
import uuid

# ------------------------------------------------------------
# CONFIGURACIÓN DE CONEXIÓN
# - Para una instancia local: URI = "bolt://localhost:7687"
# - Para Neo4j Aura o cluster: URI = "neo4j://<host>:7687"
#   (si usas neo4j:// y no es cluster, verás "Unable to retrieve routing information")
# ------------------------------------------------------------
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH_USER = os.getenv("NEO4J_USER", "neo4j")
AUTH_PASS = os.getenv("NEO4J_PASSWORD", "8UTLTRzlOW5pKf_4AsWunYzGZY2f7he2ADhGQZS4nuw")

# ------------------------------------------------------------
# MODELOS (opcionales, solo para tipado/claridad)
# ------------------------------------------------------------
@dataclass
class LineaInput:
    producto: str       # codigo del producto
    cantidad: float
    precio: float       # precioUnitario en la línea

@dataclass
class FacturaInput:
    numero: str
    fecha: str          # 'YYYY-MM-DD'
    moneda: str
    cliente: str        # codigo del cliente
    lineas: List[LineaInput]

# ------------------------------------------------------------
# DRIVER
# ------------------------------------------------------------
def get_driver():
    driver = GraphDatabase.driver(URI, auth=(AUTH_USER, AUTH_PASS))
    driver.verify_connectivity()
    return driver

# ------------------------------------------------------------
# ESQUEMA / CONSTRAINTS
# ------------------------------------------------------------
def init_schema(driver):
    cypher = [
        """
        CREATE CONSTRAINT cliente_codigo IF NOT EXISTS
        FOR (c:Cliente) REQUIRE c.codigo IS UNIQUE
        """,
        """
        CREATE CONSTRAINT producto_codigo IF NOT EXISTS
        FOR (p:Producto) REQUIRE p.codigo IS UNIQUE
        """,
        """
        CREATE CONSTRAINT factura_numero IF NOT EXISTS
        FOR (f:Factura) REQUIRE f.numero IS UNIQUE
        """,
        """
        CREATE CONSTRAINT linea_id IF NOT EXISTS
        FOR (l:Linea) REQUIRE l.id IS UNIQUE
        """
    ]
    with driver.session() as s:
        for q in cypher:
            s.run(q)

# ------------------------------------------------------------
# UPSERTS BÁSICOS
# ------------------------------------------------------------
def upsert_cliente(driver, codigo: str, nombre: str, pais: Optional[str] = None):
    q = """
    MERGE (c:Cliente {codigo:$codigo})
    SET c.nombre = $nombre,
        c.pais   = $pais
    RETURN c
    """
    with driver.session() as s:
        return s.run(q, codigo=codigo, nombre=nombre, pais=pais).single()

def upsert_producto(driver, codigo: str, nombre: str, categoria: Optional[str] = None):
    q = """
    MERGE (p:Producto {codigo:$codigo})
    SET p.nombre = $nombre,
        p.categoria = $categoria
    RETURN p
    """
    with driver.session() as s:
        return s.run(q, codigo=codigo, nombre=nombre, categoria=categoria).single()

# ------------------------------------------------------------
# CREAR FACTURA + LÍNEAS (TRANSACCIÓN)
# ------------------------------------------------------------
def create_factura_with_lineas(driver, inv: FacturaInput):
    """
    Crea/actualiza la factura y añade líneas con id UUID,
    conservando precio e historial en la entidad Línea.
    """
    def _tx(tx):
        # Cliente
        tx.run(
            "MERGE (c:Cliente {codigo:$codigo})",
            codigo=inv.cliente
        )
        # Factura
        tx.run(
            """
            MERGE (f:Factura {numero:$numero})
            SET f.fecha = date($fecha),
                f.moneda = $moneda
            WITH f
            MATCH (c:Cliente {codigo:$cliente})
            MERGE (f)-[:DE_CLIENTE]->(c)
            """,
            numero=inv.numero, fecha=inv.fecha, moneda=inv.moneda, cliente=inv.cliente
        )
        # Líneas
        for ln in inv.lineas:
            ln_id = str(uuid.uuid4())
            tx.run(
                """
                MATCH (f:Factura {numero:$numero})
                MATCH (p:Producto {codigo:$prod})
                CREATE (l:Linea {
                    id:$id, cantidad:$cant, precioUnitario:$precio
                })
                MERGE (f)-[:TIENE_LINEA]->(l)
                MERGE (l)-[:DE_PRODUCTO]->(p)
                """,
                numero=inv.numero, prod=ln.producto, id=ln_id, cant=ln.cantidad, precio=ln.precio
            )
    with driver.session() as s:
        s.execute_write(_tx)

# ------------------------------------------------------------
# CONSULTAS
# ------------------------------------------------------------
def detalle_factura(driver, numero: str) -> List[Dict[str, Any]]:
    q = """
    MATCH (f:Factura {numero:$numero})-[:TIENE_LINEA]->(l)-[:DE_PRODUCTO]->(p)
    RETURN f.numero AS factura, toString(f.fecha) AS fecha, f.moneda AS moneda,
           p.codigo AS prodCodigo, p.nombre AS prodNombre,
           l.cantidad AS cantidad, l.precioUnitario AS precioUnitario,
           l.cantidad * l.precioUnitario AS totalLinea
    ORDER BY prodCodigo
    """
    with driver.session() as s:
        return [r.data() for r in s.run(q, numero=numero)]

def ventas_por_producto(driver,
                        fecha_desde: Optional[str] = None,
                        fecha_hasta_excl: Optional[str] = None,
                        incluir_sin_venta: bool = True) -> List[Dict[str, Any]]:
    """
    Suma cantidad*precio por producto. Si incluir_sin_venta=True,
    muestra también productos sin líneas (ventaTotal = 0).
    Admite rango de fechas [desde, hasta).
    """
    where = []
    if fecha_desde:
        where.append("f.fecha >= date($desde)")
    if fecha_hasta_excl:
        where.append("f.fecha < date($hasta)")
    where_clause = ("WHERE " + " AND ".join(where)) if where else ""

    if incluir_sin_venta:
        q = f"""
        MATCH (p:Producto)
        OPTIONAL MATCH (p)<-[:DE_PRODUCTO]-(l:Linea)<-[:TIENE_LINEA]-(f:Factura)
        {where_clause}
        WITH p, sum(coalesce(l.cantidad,0) * coalesce(l.precioUnitario,0)) AS ventaTotal
        RETURN p.codigo AS producto, p.nombre AS nombre, ventaTotal
        ORDER BY ventaTotal DESC, producto
        """
    else:
        q = f"""
        MATCH (p:Producto)<-[:DE_PRODUCTO]-(l:Linea)<-[:TIENE_LINEA]-(f:Factura)
        {where_clause}
        WITH p, sum(l.cantidad * l.precioUnitario) AS ventaTotal
        RETURN p.codigo AS producto, p.nombre AS nombre, ventaTotal
        ORDER BY ventaTotal DESC, producto
        """
    params = {"desde": fecha_desde, "hasta": fecha_hasta_excl}
    with driver.session() as s:
        return [r.data() for r in s.run(q, **{k:v for k,v in params.items() if v})]

def ventas_por_cliente(driver) -> List[Dict[str, Any]]:
    q = """
    MATCH (c:Cliente)<-[:DE_CLIENTE]-(f:Factura)-[:TIENE_LINEA]->(l)
    RETURN c.codigo AS cliente, c.nombre AS nombre,
           round(sum(l.cantidad * l.precioUnitario),2) AS totalCliente
    ORDER BY totalCliente DESC, cliente
    """
    with driver.session() as s:
        return [r.data() for r in s.run(q)]

def clientes_por_producto(driver) -> List[Dict[str, Any]]:
    q = """
    MATCH (p:Producto)<-[:DE_PRODUCTO]-(l:Linea)<-[:TIENE_LINEA]-(f:Factura)-[:DE_CLIENTE]->(c:Cliente)
    RETURN p.codigo AS producto, p.nombre AS nombre,
           count(DISTINCT c) AS clientesUnicos,
           collect(DISTINCT c.codigo) AS codigosClientes
    ORDER BY producto
    """
    with driver.session() as s:
        return [r.data() for r in s.run(q)]

# ------------------------------------------------------------
# UPDATES / DELETES DE EJEMPLO
# ------------------------------------------------------------
def update_nombre_producto(driver, codigo: str, nuevo_nombre: str):
    q = """
    MATCH (p:Producto {codigo:$codigo})
    SET p.nombre = $nombre
    RETURN p.codigo AS codigo, p.nombre AS nombre
    """
    with driver.session() as s:
        rec = s.run(q, codigo=codigo, nombre=nuevo_nombre).single()
        return rec.data() if rec else None

def update_precio_linea(driver, factura_num: str, prod_codigo: str, nuevo_precio: float):
    q = """
    MATCH (f:Factura {numero:$num})-[:TIENE_LINEA]->(l)-[:DE_PRODUCTO]->(p:Producto {codigo:$prod})
    SET l.precioUnitario = $precio
    RETURN l.id AS lineaId, l.precioUnitario AS precioUnitario
    """
    with driver.session() as s:
        recs = [r.data() for r in s.run(q, num=factura_num, prod=prod_codigo, precio=nuevo_precio)]
        return recs

def delete_linea(driver, linea_id: str):
    q = "MATCH (l:Linea {id:$id}) DETACH DELETE l"
    with driver.session() as s:
        s.run(q, id=linea_id)

def delete_factura_cascade(driver, numero: str):
    q = """
    MATCH (f:Factura {numero:$num})
    OPTIONAL MATCH (f)-[:TIENE_LINEA]->(l:Linea)
    DETACH DELETE f, l
    """
    with driver.session() as s:
        s.run(q, num=numero)

# ------------------------------------------------------------
# CARGA DE DATOS DE EJEMPLO
# ------------------------------------------------------------
def seed_data(driver):
    # Catálogos
    upsert_cliente(driver, "C001", "ACME S.A.", "CR")
    upsert_cliente(driver, "C002", "Tecnova Ltda", "CR")
    upsert_cliente(driver, "C003", "Cliente sin compras", "CR")

    upsert_producto(driver, "P001", "Laptop Pro 14", "Computo")
    upsert_producto(driver, "P002", "Mouse MX", "Accesorios")
    upsert_producto(driver, "P003", "Monitor 27\"", "Displays")
    upsert_producto(driver, "P004", "Dock USB-C", "Accesorios")  # sin ventas

    # Facturas
    create_factura_with_lineas(driver, FacturaInput(
        numero="F-1001", fecha="2025-09-20", moneda="USD", cliente="C001",
        lineas=[
            LineaInput("P001", 1, 1200),
            LineaInput("P002", 2, 50),
        ]
    ))
    create_factura_with_lineas(driver, FacturaInput(
        numero="F-1002", fecha="2025-09-22", moneda="USD", cliente="C002",
        lineas=[
            LineaInput("P002", 5, 45),
            LineaInput("P003", 1, 320),
        ]
    ))
    create_factura_with_lineas(driver, FacturaInput(
        numero="F-1003", fecha="2025-10-01", moneda="USD", cliente="C001",
        lineas=[
            LineaInput("P003", 2, 300),
        ]
    ))

# ------------------------------------------------------------
# DEMO RÁPIDA
# ------------------------------------------------------------
def main():
    print(f"Conectando a Neo4j en {URI} ...")
    with get_driver() as driver:
        print("Conexión OK.")

        print("Creando esquema (constraints)...")
        init_schema(driver)

        print("Sembrando datos de ejemplo...")
        seed_data(driver)

        print("\nDetalle F-1001:")
        for row in detalle_factura(driver, "F-1001"):
            print(row)

        print("\nVentas por producto (incluye sin ventas):")
        for row in ventas_por_producto(driver, incluir_sin_venta=True):
            print(row)

        print("\nVentas por producto en Sep-Oct 2025 (incluye sin ventas):")
        for row in ventas_por_producto(driver, fecha_desde="2025-09-01", fecha_hasta_excl="2025-11-01", incluir_sin_venta=True):
            print(row)

        print("\nVentas por cliente:")
        for row in ventas_por_cliente(driver):
            print(row)

        print("\nClientes por producto:")
        for row in clientes_por_producto(driver):
            print(row)

        print("\nUpdate nombre producto P002 -> 'Mouse MX Master 3'")
        print(update_nombre_producto(driver, "P002", "Mouse MX Master 3"))

        print("\nUpdate precio línea (F-1001, P002) -> 48")
        for r in update_precio_linea(driver, "F-1001", "P002", 48):
            print(r)

        # Ejemplo de delete (comentar si no quieres borrar)
        # print("\nBorrando factura F-1003...")
        # delete_factura_cascade(driver, "F-1003")

        print("\nListo.")

if __name__ == "__main__":
    main()
