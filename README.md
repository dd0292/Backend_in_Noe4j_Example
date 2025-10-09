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
- Download from [https://neo4j.com/download/](https://neo4j.com/download/).
- Create a **new project** → **Add Database** → choose *Local DBMS*.
- Set:
    ```
    Database name: social-network
    Username: neo4j
    Password: your_password
    ```
- Start the database and open **Neo4j Browser**. 
- Python 3.10+ (`pip install -r app/requirements.txt`).
- Environment variables (set in your shell or `.env`):
  - `SUPABASE_URL` — your project URL
  - `SUPABASE_ANON_KEY` — anon/public key for the client app
  - `USER_EMAIL` / `USER_PASSWORD` — test user credentials (for app quick-demo)

## Quick start
### Setup:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```
### Run the app:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```