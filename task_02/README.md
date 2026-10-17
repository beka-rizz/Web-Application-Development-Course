# Streakline

A habit tracker. You create habits and log a check-in for each day you keep them. The API stores those days in MySQL and computes the current streak and the longest streak from the check-in history.

The stack is three containers:

- **frontend** — React page
- **backend** — FastAPI
- **db** — MySQL 8.4

## Run

Install [Docker](https://docs.docker.com/get-docker/) with Compose, then from this folder:

```bash
cp .env.example .env
```

Open `.env` and replace the two passwords. Do not commit `.env`.

Start everything:

```bash
docker compose up --build
```

When the containers are healthy:

- UI: http://localhost:8080
- API: http://localhost:3000

The first start creates the database and tables. Later starts reuse the saved data.

Stop the app with `Ctrl+C`, or from another terminal:

```bash
docker compose down
```

`docker compose down` keeps the database. To delete habits and check-ins as well:

```bash
docker compose down -v
```

## Try it

On the page, add a habit and log a few days. **Log the last 5 days** writes five check-ins so a streak shows up immediately.

The same calls work against the API directly:

```bash
curl -s http://localhost:3000/health

curl -s -X POST http://localhost:3000/habits \
  -H 'Content-Type: application/json' \
  -d '{"name":"Read 20 pages","description":"A paper book before bed."}'

curl -s -X POST http://localhost:3000/habits/1/checkins \
  -H 'Content-Type: application/json' \
  -d '{"checked_on":"2026-10-17","note":"Finished the chapter."}'

curl -s 'http://localhost:3000/habits/1/stats?as_of=2026-10-17'
```

| Method | Path | What it does |
| --- | --- | --- |
| `GET` | `/health` | Checks that the API can reach MySQL |
| `GET` | `/habits?as_of=YYYY-MM-DD` | Lists habits with streak totals |
| `POST` | `/habits` | Creates a habit (`name`, optional `description`) |
| `POST` | `/habits/{id}/checkins` | Logs one day (`checked_on`, optional `note`). One check-in per habit per day |
| `GET` | `/habits/{id}/stats?as_of=YYYY-MM-DD` | Current streak, longest streak, and each run of days |
| `DELETE` | `/habits/{id}` | Removes a habit and its check-ins |

`as_of` is the date treated as “today” when deciding whether a streak is still current. The page sends your local date. If you omit it, the API uses the current UTC date.

Interactive API docs are at http://localhost:3000/docs.

## How streaks are counted

A streak is a run of consecutive dates. MySQL groups those dates with a gaps-and-islands query: `days since 2000-01-01` minus the row number. A missed day changes the group, so a new streak starts.

The current streak counts only when the latest check-in is today or yesterday. Two missed days reset it to zero. The longest streak is the best run in the whole history.

## Configuration

Values come from `.env`. Nothing secret is stored in the source.

| Variable | Used for |
| --- | --- |
| `MYSQL_ROOT_PASSWORD` | MySQL root password |
| `MYSQL_DATABASE` | Database name |
| `MYSQL_USER` | Application database user |
| `MYSQL_PASSWORD` | Application database password |
| `BACKEND_PORT` | Host port for the API (default `3000`) |
| `FRONTEND_PORT` | Host port for the page (default `8080`) |

Inside Compose, the API connects to the host name `db` on port `3306`. MySQL is not published on the host. Data is stored in the named volume `streakline_habit_data`, so it remains after containers are stopped and created again.
