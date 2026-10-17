import asyncio
from datetime import date, datetime

from pymysql.constants.ER import DUP_ENTRY, NO_REFERENCED_ROW, NO_REFERENCED_ROW_2
from pymysql.err import IntegrityError

from app.db import execute, fetch_all


class DuplicateCheckin(Exception):
    pass


def as_int(value):
    if value is None:
        return 0
    return int(value)


def as_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)[:10]


def as_timestamp(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def map_habit(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "created_at": as_timestamp(row["created_at"]),
    }


# Consecutive dates share a key: days-since-epoch minus the row number.
# A missed day changes that key, so each group is one streak.
HABIT_STREAKS = """
  WITH dated AS (
    SELECT
      checked_on,
      DATEDIFF(checked_on, '2000-01-01')
        - ROW_NUMBER() OVER (ORDER BY checked_on) AS streak_key
    FROM checkins
    WHERE habit_id = %s
  ),
  streaks AS (
    SELECT
      MIN(checked_on) AS start_date,
      MAX(checked_on) AS end_date,
      COUNT(*) AS length
    FROM dated
    GROUP BY streak_key
  )
"""

LIST_SQL = """
  WITH dated AS (
    SELECT
      habit_id,
      checked_on,
      DATEDIFF(checked_on, '2000-01-01')
        - ROW_NUMBER() OVER (PARTITION BY habit_id ORDER BY checked_on) AS streak_key
    FROM checkins
  ),
  streaks AS (
    SELECT
      habit_id,
      MIN(checked_on) AS start_date,
      MAX(checked_on) AS end_date,
      COUNT(*) AS length
    FROM dated
    GROUP BY habit_id, streak_key
  ),
  summary AS (
    SELECT
      habit_id,
      MAX(length) AS longest_streak,
      MAX(
        CASE
          WHEN end_date >= DATE_SUB(%s, INTERVAL 1 DAY) THEN length
          ELSE 0
        END
      ) AS current_streak,
      MAX(end_date) AS last_checkin,
      SUM(length) AS total_checkins
    FROM streaks
    GROUP BY habit_id
  )
  SELECT
    h.id,
    h.name,
    h.description,
    h.created_at,
    COALESCE(s.longest_streak, 0) AS longest_streak,
    COALESCE(s.current_streak, 0) AS current_streak,
    s.last_checkin,
    COALESCE(s.total_checkins, 0) AS total_checkins,
    IF(c.habit_id IS NULL, 0, 1) AS checked_in_on
  FROM habits h
  LEFT JOIN summary s ON s.habit_id = h.id
  LEFT JOIN (
    SELECT habit_id
    FROM checkins
    WHERE checked_on = %s
  ) c ON c.habit_id = h.id
  ORDER BY h.created_at DESC, h.id DESC
"""


async def list_habits(pool, as_of):
    rows = await fetch_all(pool, LIST_SQL, (as_of, as_of))
    return [
        {
            **map_habit(row),
            "current_streak": as_int(row["current_streak"]),
            "longest_streak": as_int(row["longest_streak"]),
            "total_checkins": as_int(row["total_checkins"]),
            "last_checkin": as_date(row["last_checkin"]),
            "checked_in_on": bool(as_int(row["checked_in_on"])),
        }
        for row in rows
    ]


async def create_habit(pool, name, description):
    habit_id, _rowcount = await execute(
        pool,
        "INSERT INTO habits (name, description) VALUES (%s, %s)",
        (name, description),
    )
    rows = await fetch_all(
        pool,
        "SELECT id, name, description, created_at FROM habits WHERE id = %s",
        (habit_id,),
    )
    return map_habit(rows[0])


async def delete_habit(pool, habit_id):
    _last_id, rowcount = await execute(
        pool,
        "DELETE FROM habits WHERE id = %s",
        (habit_id,),
    )
    return rowcount > 0


async def add_checkin(pool, habit_id, checked_on, note):
    existing = await fetch_all(
        pool,
        "SELECT id FROM habits WHERE id = %s",
        (habit_id,),
    )
    if not existing:
        return None

    try:
        checkin_id, _rowcount = await execute(
            pool,
            "INSERT INTO checkins (habit_id, checked_on, note) VALUES (%s, %s, %s)",
            (habit_id, checked_on, note),
        )
    except IntegrityError as error:
        code = error.args[0]
        if code == DUP_ENTRY:
            raise DuplicateCheckin from error
        if code in (NO_REFERENCED_ROW, NO_REFERENCED_ROW_2):
            return None
        raise

    return {
        "id": checkin_id,
        "habit_id": habit_id,
        "checked_on": checked_on,
        "note": note,
    }


async def get_stats(pool, habit_id, as_of):
    habits = await fetch_all(
        pool,
        "SELECT id, name, description, created_at FROM habits WHERE id = %s",
        (habit_id,),
    )
    if not habits:
        return None

    summary_sql = f"""
      {HABIT_STREAKS}
      SELECT
        COALESCE(MAX(length), 0) AS longest_streak,
        COALESCE(
          MAX(
            CASE
              WHEN end_date >= DATE_SUB(%s, INTERVAL 1 DAY) THEN length
              ELSE 0
            END
          ),
          0
        ) AS current_streak,
        MAX(end_date) AS last_checkin,
        COALESCE(SUM(length), 0) AS total_checkins
      FROM streaks
    """
    streak_sql = f"""
      {HABIT_STREAKS}
      SELECT
        start_date,
        end_date,
        length,
        end_date >= DATE_SUB(%s, INTERVAL 1 DAY) AS active
      FROM streaks
      ORDER BY start_date DESC
    """
    checkin_sql = """
      SELECT id, checked_on, note
      FROM checkins
      WHERE habit_id = %s
      ORDER BY checked_on DESC
    """

    summary_rows, streak_rows, checkin_rows = await asyncio.gather(
        fetch_all(pool, summary_sql, (habit_id, as_of)),
        fetch_all(pool, streak_sql, (habit_id, as_of)),
        fetch_all(pool, checkin_sql, (habit_id,)),
    )

    summary = summary_rows[0] if summary_rows else {}
    checkins = [
        {
            "id": row["id"],
            "checked_on": as_date(row["checked_on"]),
            "note": row["note"],
        }
        for row in checkin_rows
    ]

    return {
        "habit": map_habit(habits[0]),
        "as_of": as_of,
        "total_checkins": as_int(summary.get("total_checkins")),
        "current_streak": as_int(summary.get("current_streak")),
        "longest_streak": as_int(summary.get("longest_streak")),
        "last_checkin": as_date(summary.get("last_checkin")),
        "checked_in_on": any(checkin["checked_on"] == as_of for checkin in checkins),
        "streaks": [
            {
                "start_date": as_date(row["start_date"]),
                "end_date": as_date(row["end_date"]),
                "length": as_int(row["length"]),
                "active": bool(as_int(row["active"])),
            }
            for row in streak_rows
        ],
        "checkins": checkins,
    }
