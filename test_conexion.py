import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
)
driver.verify_connectivity()

with driver.session(database=os.getenv("NEO4J_DATABASE")) as session:
    resultado = session.run("RETURN 'Conexión exitosa a AuraDB' AS mensaje")
    print(resultado.single()["mensaje"])

driver.close()