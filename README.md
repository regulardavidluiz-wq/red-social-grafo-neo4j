# Red Social con Grafo en Neo4j AuraDB (Python)

Aplicación en Python conectada a **Neo4j AuraDB** (base de datos NoSQL orientada a grafos en la nube) para gestionar usuarios, relaciones (`SIGUE`, `INTERESADO_EN`), operaciones CRUD y consultas de grafo (vecindad / amigos de amigos, camino más corto y búsqueda por interés).

## Requerimientos
- Python 3.9+
- Instancia activa en **Neo4j AuraDB**
- Dependencias en `requirements.txt`

## Instalación
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt