import dotenv
import os
from neo4j import GraphDatabase

load_status = dotenv.load_dotenv(".env")
if load_status is False:
    raise RuntimeError('Environment variables not loaded.')

URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("Connection established.")

    records, summary, keys = driver.execute_query(
        "MATCH (n) RETURN n",
        database_="neo4j"  # Specify the database name if needed
    )

    # Print each node's data
    for record in records:
        node = record["n"]
        print(node)