# Streakline API

Base URL when the stack is running: `http://localhost:3000`

The browser page does not call that port. nginx on port 8080 proxies `/api/...` to these same paths.

Send JSON bodies with `Content-Type: application/json`. Successful deletes return `204` and an empty body. Every other response is JSON. Errors use one shape:

```json
{"error": "Habit not found."}
```

| Status | When |
| --- | --- |
| 400 | The id, date, or text is invalid, or the JSON body is not an object |
| 404 | The URL is unknown, or the habit or check-in does not exist |
| 405 | The method is not allowed on that path |
| 409 | This habit already has a check-in on that date |
| 503 | The database is unavailable |
| 500 | Unexpected server error |

Ids are positive integers. Deleted ids are not reused. A habit may share its name with another habit. A habit may have only one check-in per date. The same date may be logged on two different habits.

## Dates and `as_of`

Dates are `YYYY-MM-DD`, from `2000-01-01` through tomorrow in UTC.

`as_of` is the date treated as “today” when the API decides whether a streak is still current. List, update, and stats all accept it as a query parameter. If you omit it, the API uses the current UTC date. An invalid `as_of` returns 400:

```json
{"error": "Date must be YYYY-MM-DD, from 2000-01-01 through tomorrow."}
```

On create, a missing or empty `checked_on` means today in UTC.

Text fields are trimmed. `description` and `note` are JSON `null` when empty. Limits:

| Field | Required | Max length |
| --- | --- | --- |
| `name` | yes | 120 |
| `description` | no | 500 |
| `note` | no | 280 |

`PATCH` changes only the fields you send. An empty `PATCH` body returns 400. A missing field stays as it is.

## Streaks

Check-in dates are grouped into runs of consecutive days. A missed day starts a new run.

A run is **active** when its last day is yesterday or any later day relative to `as_of` (`end_date >= as_of - 1 day`). The **current streak** is the longest active run, or 0 when none are active. The **longest streak** is the longest run in the whole history. `checked_in_on` is true only when `as_of` itself has a check-in.

For a normal history, where every check-in is on or before `as_of`, that means: the current streak survives today and yesterday, and two missed days reset it to zero.

Example. Check-ins on 1, 2, 3, and 5 October 2026:

| `as_of` | Current | Longest | Why |
| --- | --- | --- | --- |
| 2026-10-04 | 3 | 3 | The 1–3 Oct run ends on yesterday. The later one-day run is active too, and 3 is longer |
| 2026-10-05 | 1 | 3 | The latest run is only 5 Oct |
| 2026-10-06 | 1 | 3 | 5 Oct is yesterday, so that one-day run is still current |
| 2026-10-07 | 0 | 3 | 5 Oct is now two days behind |

## Habit object

List, create, and update all return this object. Streak fields depend on `as_of`.

```json
{
  "id": 1,
  "name": "Read 20 pages",
  "description": "A paper book before bed.",
  "created_at": "2026-10-31 05:21:00",
  "updated_at": "2026-10-31 05:21:00",
  "current_streak": 0,
  "longest_streak": 0,
  "total_checkins": 0,
  "last_checkin": null,
  "checked_in_on": false
}
```

`created_at` and `updated_at` are UTC, `YYYY-MM-DD HH:MM:SS`.

## Check-in object

```json
{
  "id": 4,
  "habit_id": 1,
  "checked_on": "2026-10-17",
  "note": "Finished the chapter."
}
```

## Health

### `GET /health`

Checks that the API can reach MySQL.

```json
{"status": "ok", "database": "up"}
```

If MySQL cannot be reached: `503` and `{"error": "Database unavailable."}`.

## Habits

### `GET /habits?as_of=YYYY-MM-DD`

Lists habits, newest first, with streak totals.

```json
{
  "as_of": "2026-10-17",
  "habits": []
}
```

### `POST /habits`

Creates a habit. `201` and the habit object.

```json
{"name": "Read 20 pages", "description": "A paper book before bed."}
```

| Error | When |
| --- | --- |
| 400 `name is required.` | `name` is missing or blank |
| 400 `name must be 120 characters or fewer.` | `name` is too long or not a string |
| 400 `description must be 500 characters or fewer.` | `description` is too long or not a string |
| 400 `Request body must be valid JSON.` | The body is not JSON |
| 400 `Request body must be a JSON object.` | The JSON value is an array or a string |

### `PATCH /habits/{id}?as_of=YYYY-MM-DD`

Updates only the fields in the body. Returns the habit object.

```json
{"description": "Thirty pages, not twenty."}
```

`400` `Provide name or description to update.` when the body has neither field. Unknown fields are ignored. The same 400 errors as create apply. `404` `Habit not found.` when no habit has that id. `400` `Habit id must be a positive integer.` when the id is `0`, negative, or not an integer.

### `DELETE /habits/{id}`

Deletes the habit and its check-ins. `204` with an empty body. `404` `Habit not found.` if it is already gone.

## Check-ins

The ledger for one habit comes back inside `GET /habits/{id}/stats`. These two routes create and delete a day.

### `POST /habits/{id}/checkins`

Logs one day. `201` and the check-in object. `checked_on` is optional and defaults to today UTC. `note` is optional.

```json
{"checked_on": "2026-10-17", "note": "Finished the chapter."}
```

| Error | When |
| --- | --- |
| 400 | `checked_on` is not a date in range, or `note` is longer than 280 characters |
| 404 `Habit not found.` | The habit does not exist |
| 409 `Already checked in on this date.` | This habit already has that day |

### `DELETE /habits/{id}/checkins/{checkin_id}`

Deletes that check-in and frees the day. `204` with an empty body. Streak totals on the next read no longer include that day. `404` `Habit not found.` when the habit does not exist. `404` `Check-in not found.` when that day is not on this habit. `400` when either id is not a positive integer.

## Stats

### `GET /habits/{id}/stats?as_of=YYYY-MM-DD`

Current streak, longest streak, each run, and the check-in ledger.

```json
{
  "habit": {
    "id": 1,
    "name": "Read 20 pages",
    "description": "A paper book before bed.",
    "created_at": "2026-10-31 05:21:00",
    "updated_at": "2026-10-31 05:21:00"
  },
  "as_of": "2026-10-17",
  "total_checkins": 4,
  "current_streak": 1,
  "longest_streak": 3,
  "last_checkin": "2026-10-17",
  "checked_in_on": true,
  "streaks": [
    {
      "start_date": "2026-10-17",
      "end_date": "2026-10-17",
      "length": 1,
      "active": true
    },
    {
      "start_date": "2026-10-01",
      "end_date": "2026-10-03",
      "length": 3,
      "active": false
    }
  ],
  "checkins": [
    {"id": 4, "habit_id": 1, "checked_on": "2026-10-17", "note": null}
  ]
}
```

Runs are newest first. `active` uses the same rule as the current streak. `404` `Habit not found.` when the id does not exist.
