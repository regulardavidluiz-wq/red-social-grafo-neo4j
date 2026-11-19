from db import DB, con_reintento

USUARIOS = [
    {"id": "u1", "nombre": "Ana", "ciudad": "Mérida"},
    {"id": "u2", "nombre": "Luis", "ciudad": "Mérida"},
    {"id": "u3", "nombre": "Carla", "ciudad": "Cancún"},
    {"id": "u4", "nombre": "Pedro", "ciudad": "Valladolid"},
    {"id": "u5", "nombre": "Sofía", "ciudad": "Mérida"},
    {"id": "u6", "nombre": "Diego", "ciudad": "Progreso"},
    {"id": "u7", "nombre": "Mariana", "ciudad": "Cancún"},
    {"id": "u8", "nombre": "Jorge", "ciudad": "Mérida"},
]

INTERESES = ["Música", "Deportes", "Cine", "Tecnología", "Viajes"]

SIGUE = [
    ["u1", "u2"], ["u2", "u3"], ["u3", "u4"], ["u1", "u5"],
    ["u5", "u6"], ["u6", "u7"], ["u7", "u8"], ["u2", "u5"],
    ["u4", "u8"], ["u8", "u1"],
]

INTERESADO = [
    ["u1", "Música"], ["u1", "Tecnología"], ["u2", "Deportes"],
    ["u3", "Cine"], ["u4", "Viajes"], ["u5", "Música"],
    ["u6", "Tecnología"], ["u7", "Cine"], ["u8", "Deportes"],
]


def _cargar(tx):
    tx.run("MATCH (n) DETACH DELETE n")
    tx.run("UNWIND $us AS u CREATE (:Usuario {id:u.id, nombre:u.nombre, ciudad:u.ciudad})",
           us=USUARIOS)
    tx.run("UNWIND $its AS n CREATE (:Interes {nombre:n})", its=INTERESES)
    tx.run("UNWIND $rels AS r "
           "MATCH (a:Usuario {id:r[0]}), (b:Usuario {id:r[1]}) "
           "CREATE (a)-[:SIGUE {desde: date()}]->(b)", rels=SIGUE)
    tx.run("UNWIND $rels AS r "
           "MATCH (a:Usuario {id:r[0]}), (b:Interes {nombre:r[1]}) "
           "CREATE (a)-[:INTERESADO_EN]->(b)", rels=INTERESADO)
    return tx.run("MATCH (n) RETURN count(n) AS c").single()["c"]


def sembrar(driver):
    with driver.session(database=DB) as s:
        s.run("CREATE CONSTRAINT usuario_id IF NOT EXISTS "
              "FOR (u:Usuario) REQUIRE u.id IS UNIQUE")
        s.run("CREATE CONSTRAINT interes_nombre IF NOT EXISTS "
              "FOR (i:Interes) REQUIRE i.nombre IS UNIQUE")
        return s.execute_write(_cargar)


if __name__ == "__main__":
    total = con_reintento(sembrar)
    print(f"Seeding completo: {total} nodos creados")