# Space Bounty Hunters

REST API for wanted criminals and hunt logs. FastAPI and MySQL.

## Docker Compose

```bash
docker compose up --build
```

API: `http://127.0.0.1:8000`

MySQL is published on `localhost:3306` as user `root`, password `root`, database `bounty_hunters`. `schema.sql` loads on the first start.

## Database

```bash
mysql -u root < schema.sql
```

If root has a password, pass `-p`. To point the app at another server, set `DATABASE_URL` or `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT`, and `MYSQL_DATABASE`.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API base: `http://127.0.0.1:8000`

Import `Space_Bounty_Hunters.postman_collection.json` into Postman. The collection variable `baseUrl` is `http://127.0.0.1:8000`.
