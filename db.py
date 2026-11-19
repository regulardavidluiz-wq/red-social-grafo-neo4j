import os
import time
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

DB = (os.getenv("NEO4J_DATABASE") or "").strip() or None


def sesion(driver):
    """Abre sesión usando NEO4J_DATABASE si existe, o la base por defecto de AuraDB."""
    if DB:
        return driver.session(database=DB)
    return driver.session()


def get_driver(intentos=10):
    for i in range(1, intentos + 1):
        try:
            driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI"),
                auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
            )
            driver.verify_connectivity()
            return driver
        except Exception:
            print(f"Conexión intento {i}/{intentos} falló, reintentando...")
            time.sleep(3)
    raise RuntimeError("No se pudo conectar a AuraDB")


def con_reintento(funcion, intentos=10):
    """Ejecuta funcion(driver) y reintenta si la conexión se cae."""
    for i in range(1, intentos + 1):
        driver = None
        try:
            driver = get_driver()
            return funcion(driver)
        except Exception as e:
            print(f"Operación intento {i}/{intentos} falló: {type(e).__name__}")
            time.sleep(3)
        finally:
            if driver:
                driver.close()
    raise RuntimeError("La operación falló tras todos los reintentos")