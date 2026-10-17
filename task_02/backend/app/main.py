import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pymysql.err import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse, Response

from app.db import connect_pool, fetch_all, require_env
from app.habits import DuplicateCheckin, add_checkin, create_habit, delete_habit, get_stats, list_habits
from app.validate import clean_text, parse_id, parse_iso_date, resolve_as_of, today_utc, add_days

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("streakline")

DATE_ERROR = "Date must be YYYY-MM-DD, from 2000-01-01 through tomorrow."


class ApiError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


@asynccontextmanager
async def lifespan(app: FastAPI):
    require_env()
    app.state.pool = await connect_pool()
    yield
    app.state.pool.close()
    await app.state.pool.wait_closed()


app = FastAPI(title="Streakline", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApiError)
async def api_error(_request, exc: ApiError):
    return JSONResponse(status_code=exc.status, content={"error": exc.message})


@app.exception_handler(StarletteHTTPException)
async def http_error(_request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(status_code=404, content={"error": "Not found."})
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


@app.exception_handler(RequestValidationError)
async def validation_error(_request, exc: RequestValidationError):
    message = "Request body must be valid JSON."
    for error in exc.errors():
        location = error.get("loc", ())
        if "as_of" in location or "checked_on" in location:
            message = DATE_ERROR
            break
        if "habit_id" in location:
            message = "Habit id must be a positive integer."
            break
    return JSONResponse(status_code=400, content={"error": message})


@app.exception_handler(Exception)
async def unexpected(request, exc: Exception):
    if isinstance(exc, ApiError):
        return JSONResponse(status_code=exc.status, content={"error": exc.message})
    if isinstance(exc, RequestValidationError):
        return await validation_error(request, exc)
    if isinstance(exc, StarletteHTTPException):
        if exc.status_code == 404:
            return JSONResponse(status_code=404, content={"error": "Not found."})
        return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})
    if isinstance(exc, OperationalError):
        log.exception("database unavailable")
        return JSONResponse(status_code=503, content={"error": "Database unavailable."})
    log.exception("request failed")
    return JSONResponse(status_code=500, content={"error": "Unexpected server error."})


async def read_json(request: Request):
    raw = await request.body()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ApiError(400, "Request body must be valid JSON.") from error
    if not isinstance(data, dict):
        raise ApiError(400, "Request body must be a JSON object.")
    return data


def require_habit_id(value):
    habit_id = parse_id(value)
    if habit_id is None:
        raise ApiError(400, "Habit id must be a positive integer.")
    return habit_id


def require_as_of(value):
    as_of = resolve_as_of(value)
    if as_of is None:
        raise ApiError(400, DATE_ERROR)
    return as_of


@app.get("/health")
async def health(request: Request):
    await fetch_all(request.app.state.pool, "SELECT 1")
    return {"status": "ok", "database": "up"}


@app.get("/habits")
async def get_habits(request: Request, as_of: str | None = None):
    day = require_as_of(as_of)
    habits = await list_habits(request.app.state.pool, day)
    return {"as_of": day, "habits": habits}


@app.post("/habits", status_code=201)
async def post_habit(request: Request):
    body = await read_json(request)
    name_error, name = clean_text(body.get("name"), 120)
    if name_error or not name:
        if name_error:
            raise ApiError(400, "name must be 120 characters or fewer.")
        raise ApiError(400, "name is required.")

    description_error, description = clean_text(body.get("description"), 500)
    if description_error:
        raise ApiError(400, "description must be 500 characters or fewer.")

    return await create_habit(request.app.state.pool, name, description)


@app.get("/habits/{habit_id}/stats")
async def habit_stats(habit_id: str, request: Request, as_of: str | None = None):
    parsed_id = require_habit_id(habit_id)
    day = require_as_of(as_of)
    stats = await get_stats(request.app.state.pool, parsed_id, day)
    if stats is None:
        raise ApiError(404, "Habit not found.")
    return stats


@app.post("/habits/{habit_id}/checkins", status_code=201)
async def post_checkin(habit_id: str, request: Request):
    parsed_id = require_habit_id(habit_id)
    body = await read_json(request)

    raw_date = body.get("checked_on")
    if raw_date is None or raw_date == "":
        checked_on = today_utc()
    else:
        checked_on = parse_iso_date(raw_date)
    if checked_on is None:
        raise ApiError(400, DATE_ERROR)

    latest = add_days(today_utc(), 1)
    if checked_on < "2000-01-01" or checked_on > latest:
        raise ApiError(400, DATE_ERROR)

    note_error, note = clean_text(body.get("note"), 280)
    if note_error:
        raise ApiError(400, "note must be 280 characters or fewer.")

    try:
        checkin = await add_checkin(request.app.state.pool, parsed_id, checked_on, note)
    except DuplicateCheckin as error:
        raise ApiError(409, "Already checked in on this date.") from error
    if checkin is None:
        raise ApiError(404, "Habit not found.")
    return checkin


@app.delete("/habits/{habit_id}", status_code=204)
async def remove_habit(habit_id: str, request: Request):
    parsed_id = require_habit_id(habit_id)
    removed = await delete_habit(request.app.state.pool, parsed_id)
    if not removed:
        raise ApiError(404, "Habit not found.")
    return Response(status_code=204)
