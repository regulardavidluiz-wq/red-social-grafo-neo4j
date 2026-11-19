import time
from neo4j.exceptions import ClientError
from db import con_reintento, sesion


def q(query, **params):
    """Ejecuta una consulta Cypher con reintento ante fallos transitorios de conexión."""
    def trabajo(driver):
        try:
            with sesion(driver) as s:
                return s.run(query, **params).data()
        except ClientError as e:
            if "not found" in str(e).lower():
                raise
            return e

    res = con_reintento(trabajo)
    if isinstance(res, Exception):
        print("Error de la base de datos:", getattr(res, "message", str(res)))
        return []
    return res


# ---------- CRUD ----------

def listar_usuarios():
    rows = q(
        "MATCH (u:Usuario) "
        "RETURN u.id AS id, u.nombre AS nombre, u.ciudad AS ciudad "
        "ORDER BY u.id"
    )
    if not rows:
        print("  No hay usuarios registrados.")
        return
    for r in rows:
        print(f"  {r['id']:<12} {r['nombre']:<14} {r['ciudad']}")


def crear_usuario():
    nombre = input("Nombre: ").strip()
    ciudad = input("Ciudad: ").strip()
    if not nombre or not ciudad:
        print("Nombre y ciudad son obligatorios.")
        return
    uid = "u" + str(int(time.time()))
    q(
        "CREATE (:Usuario {id: $id, nombre: $nombre, ciudad: $ciudad})",
        id=uid,
        nombre=nombre,
        ciudad=ciudad,
    )
    print(f"Usuario creado con id: {uid}")


def ver_usuario():
    uid = input("ID del usuario: ").strip()
    rows = q(
        "MATCH (u:Usuario {id: $id}) "
        "OPTIONAL MATCH (u)-[:INTERESADO_EN]->(i:Interes) "
        "OPTIONAL MATCH (u)-[:SIGUE]->(s:Usuario) "
        "RETURN u.nombre AS nombre, u.ciudad AS ciudad, "
        "collect(DISTINCT i.nombre) AS intereses, "
        "collect(DISTINCT s.nombre) AS siguiendo",
        id=uid,
    )
    if not rows or rows[0]["nombre"] is None:
        print("No existe ese usuario.")
        return
    r = rows[0]
    intereses = ", ".join([x for x in r["intereses"] if x]) or "ninguno"
    siguiendo = ", ".join([x for x in r["siguiendo"] if x]) or "nadie"
    print(f"  Nombre:    {r['nombre']}")
    print(f"  Ciudad:    {r['ciudad']}")
    print(f"  Intereses: {intereses}")
    print(f"  Siguiendo: {siguiendo}")


def actualizar_ciudad():
    uid = input("ID del usuario: ").strip()
    nueva_ciudad = input("Nueva ciudad: ").strip()
    if not nueva_ciudad:
        print("La ciudad no puede estar vacía.")
        return
    rows = q(
        "MATCH (u:Usuario {id: $id}) "
        "SET u.ciudad = $ciudad "
        "RETURN u.id AS id, u.nombre AS nombre, u.ciudad AS ciudad",
        id=uid,
        ciudad=nueva_ciudad,
    )
    if not rows:
        print("No se encontró el usuario.")
        return
    print(f"Actualizado: {rows[0]['nombre']} ahora está en {rows[0]['ciudad']}.")


def eliminar_usuario():
    uid = input("ID del usuario a eliminar: ").strip()
    rows = q(
        "MATCH (u:Usuario {id: $id}) "
        "WITH u, u.nombre AS nombre "
        "DETACH DELETE u "
        "RETURN nombre",
        id=uid,
    )
    if not rows:
        print("No existe ese usuario.")
        return
    print(f"Usuario '{rows[0]['nombre']}' (id: {uid}) eliminado junto con sus relaciones.")


def seguir_usuario():
    origen_id = input("Tu ID de usuario: ").strip()
    destino_id = input("ID del usuario a seguir: ").strip()
    if origen_id == destino_id:
        print("Un usuario no puede seguirse a sí mismo.")
        return
    rows = q(
        "MATCH (a:Usuario {id: $origen}), (b:Usuario {id: $destino}) "
        "MERGE (a)-[r:SIGUE]->(b) "
        "ON CREATE SET r.desde = date() "
        "RETURN a.nombre AS origen, b.nombre AS destino",
        origen=origen_id,
        destino=destino_id,
    )
    if not rows:
        print("Verifica que ambos IDs de usuario existan.")
        return
    print(f"{rows[0]['origen']} ahora sigue a {rows[0]['destino']}.")


# ---------- CONSULTAS ESPECIALIZADAS DE GRAFO ----------

def amigos_de_amigos():
    """Vecindad de 2 saltos: usuarios seguidos por quienes sigo, excluyéndome y a quienes ya sigo."""
    uid = input("ID del usuario para recomendar conexiones: ").strip()
    rows = q(
        "MATCH (u:Usuario {id: $id})-[:SIGUE]->(:Usuario)-[:SIGUE]->(fof:Usuario) "
        "WHERE fof.id <> $id AND NOT (u)-[:SIGUE]->(fof) "
        "RETURN fof.id AS id, fof.nombre AS nombre, fof.ciudad AS ciudad, "
        "count(*) AS puentes "
        "ORDER BY puentes DESC, nombre ASC",
        id=uid,
    )
    if not rows:
        print("  No hay recomendaciones de segundo grado disponibles.")
        return
    for r in rows:
        print(f"  {r['nombre']} ({r['id']}) - {r['ciudad']} | conexiones en común: {r['puentes']}")


def camino_mas_corto():
    """Camino más corto dirigido entre dos usuarios usando shortestPath."""
    origen_id = input("ID usuario origen: ").strip()
    destino_id = input("ID usuario destino: ").strip()
    rows = q(
        "MATCH (a:Usuario {id: $origen}), (b:Usuario {id: $destino}), "
        "p = shortestPath((a)-[:SIGUE*1..6]->(b)) "
        "RETURN [n IN nodes(p) | n.nombre] AS ruta, length(p) AS saltos",
        origen=origen_id,
        destino=destino_id,
    )
    if not rows:
        print("  No existe una ruta dirigida entre esos usuarios (en hasta 6 saltos).")
        return
    ruta = " -> ".join(rows[0]["ruta"])
    print(f"  Ruta ({rows[0]['saltos']} saltos): {ruta}")


def usuarios_por_interes():
    """Traversal por etiqueta e interés compartido."""
    interes = input("Nombre del interés: ").strip()
    rows = q(
        "MATCH (u:Usuario)-[:INTERESADO_EN]->(i:Interes) "
        "WHERE toLower(i.nombre) = toLower($interes) "
        "RETURN u.id AS id, u.nombre AS nombre, u.ciudad AS ciudad, i.nombre AS interes",
        interes=interes,
    )
    if not rows:
        print("  Ningún usuario tiene registrado ese interés.")
        return
    for r in rows:
        print(f"  {r['id']} | {r['nombre']} ({r['ciudad']}) -> {r['interes']}")


def menu():
    opciones = {
        "1": ("Listar usuarios", listar_usuarios),
        "2": ("Crear usuario", crear_usuario),
        "3": ("Ver detalle de usuario", ver_usuario),
        "4": ("Actualizar ciudad de usuario", actualizar_ciudad),
        "5": ("Seguir a otro usuario (crear relación SIGUE)", seguir_usuario),
        "6": ("Eliminar usuario", eliminar_usuario),
        "7": ("Recomendación: amigos de amigos (vecindad)", amigos_de_amigos),
        "8": ("Camino más corto entre dos usuarios", camino_mas_corto),
        "9": ("Buscar usuarios por interés", usuarios_por_interes),
    }
    while True:
        print("\n=== RED SOCIAL EN NEO4J AURADB ===")
        for k, (desc, _) in opciones.items():
            print(f"  {k}. {desc}")
        print("  0. Salir")
        eleccion = input("Elige una opción: ").strip()
        if eleccion == "0":
            break
        accion = opciones.get(eleccion)
        if accion:
            accion[1]()
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    menu()