# Backend — Neo4j (Example)

By: 
 - David Chaves Mena
 - Sergio Zúñiga Castillo
 - Igancio Madriz Ortiz
 - Rachel Leiva
 - Rodrigo Donoso

**Short**: Lab project using **Neo4j** as a graph database to model a small social network.

**Spec**: follows the [lab_instructions](Lab_Noe4j.pdf) (models, CRUD, seeds, deliverables).

## Repo structure
```bash
.
├─ README.md
├─ db/
├─ app/
│  ├─ .env
│  ├─ main.py
│  └─ requirements.txt
├─ tests/
└─ deliverables/
```

## Prerequisites
- Download from [Neo4j Desktop](https://neo4j.com/download/).
- Create/connect to a "Local instace" or "Remote connection" 
- Python 3.10+ (`pip install -r app/requirements.txt`).
- Environment variables (set in your shell or `.env`):
  - `NEO4J_URI` — your project URL
  - `NEO4J_USER` — public user name for the client app
  - `NEO4J_PASSWORD` — user password

## Quick start
### Setup:
1. Open Supabase Neo4j Desktop → Tools → Query.
3. Run `db/schema.cypher` to insert the schema.
4. Run `db/seed.cypher` to add mock data.

### Run the app:
```bash
cd app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```