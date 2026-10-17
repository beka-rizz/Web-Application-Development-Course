import { useCallback, useEffect, useState } from "react";
import { createCheckin, createHabit, deleteHabit, fetchHabits, fetchStats } from "./api.js";
import { addDays, buildDays, localISODate, prettyDate } from "./dates.js";

const SUGGESTIONS = [
  { name: "Read 20 pages", description: "A paper book, before the phone comes out." },
  { name: "Morning walk", description: "Ten minutes outside." },
  { name: "Water before coffee", description: "One full glass, then the kettle." },
];

export default function App() {
  const [asOf] = useState(() => localISODate());
  const [habits, setHabits] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [formError, setFormError] = useState("");
  const [detailError, setDetailError] = useState("");
  const [pending, setPending] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [checkDate, setCheckDate] = useState(asOf);
  const [note, setNote] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  const applyHabits = useCallback((data, preferredId) => {
    setHabits(data.habits);
    const ids = data.habits.map((habit) => habit.id);
    const nextId = ids.includes(preferredId) ? preferredId : (ids[0] ?? null);
    setSelectedId(nextId);
    return nextId;
  }, []);

  const load = useCallback(
    async (preferredId) => {
      const data = await fetchHabits(asOf);
      const nextId = applyHabits(data, preferredId);
      setStats(nextId ? await fetchStats(nextId, asOf) : null);
      return nextId;
    },
    [applyHabits, asOf],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchHabits(asOf);
        if (cancelled) return;
        const nextId = applyHabits(data, null);
        if (nextId) setStats(await fetchStats(nextId, asOf));
      } catch (error) {
        if (!cancelled) setPageError(error.message || "Could not reach the API.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [applyHabits, asOf]);

  useEffect(() => {
    setCheckDate(asOf);
    setNote("");
    setConfirmDelete(false);
    setDetailError("");
  }, [selectedId, asOf]);

  async function openHabit(id) {
    setSelectedId(id);
    setStats(null);
    try {
      setStats(await fetchStats(id, asOf));
    } catch (error) {
      setDetailError(error.message);
    }
  }

  async function onCreate(event) {
    event.preventDefault();
    setFormError("");
    setPending("create");
    try {
      const habit = await createHabit({
        name,
        description: description || null,
      });
      setName("");
      setDescription("");
      setPageError("");
      await load(habit.id);
    } catch (error) {
      setFormError(error.message);
    } finally {
      setPending("");
    }
  }

  async function logDate(id, date, checkinNote) {
    await createCheckin(id, {
      checked_on: date,
      note: checkinNote || null,
    });
    setPageError("");
    await load(id);
  }

  async function logToday(id) {
    setDetailError("");
    setPending(`today-${id}`);
    try {
      await logDate(id, asOf, null);
    } catch (error) {
      setDetailError(error.message);
    } finally {
      setPending("");
    }
  }

  async function onCheckin(event) {
    event.preventDefault();
    if (!selectedId) return;
    setDetailError("");
    setPending("checkin");
    try {
      await logDate(selectedId, checkDate, note);
      setNote("");
    } catch (error) {
      setDetailError(error.message);
    } finally {
      setPending("");
    }
  }

  async function logRecentRun() {
    if (!selectedId) return;
    setDetailError("");
    setPending("run");
    try {
      const dates = [0, 1, 2, 3, 4].map((offset) => addDays(asOf, -offset));
      await Promise.all(
        dates.map(async (date) => {
          try {
            await createCheckin(selectedId, { checked_on: date });
          } catch (error) {
            if (error.status !== 409) throw error;
          }
        }),
      );
      await load(selectedId);
    } catch (error) {
      setDetailError(error.message);
    } finally {
      setPending("");
    }
  }

  async function onDelete() {
    if (!selectedId) return;
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    setPending("delete");
    setDetailError("");
    try {
      await deleteHabit(selectedId);
      await load(null);
    } catch (error) {
      setDetailError(error.message);
    } finally {
      setPending("");
      setConfirmDelete(false);
    }
  }

  const selected = habits.find((habit) => habit.id === selectedId) ?? null;
  const statsMatch = stats && selected && stats.habit.id === selected.id ? stats : null;
  const loggedOnFormDate = Boolean(
    statsMatch?.checkins.some((checkin) => checkin.checked_on === checkDate),
  );
  const longest = statsMatch?.longest_streak || 1;

  return (
    <div className="page">
      <header className="masthead">
        <div>
          <p className="eyebrow">Habit tracker</p>
          <h1>Streakline</h1>
          <p className="lede">
            Log the days you show up. The API calculates the current streak and the longest streak.
          </p>
        </div>
        <p className="today">
          <span>Today</span>
          <strong>{prettyDate(asOf)}</strong>
        </p>
      </header>

      {pageError ? (
        <div className="banner" role="alert">
          <p>{pageError}</p>
          <button
            type="button"
            onClick={() => {
              setLoading(true);
              setPageError("");
              load(selectedId)
                .catch((error) => setPageError(error.message))
                .finally(() => setLoading(false));
            }}
          >
            Retry
          </button>
        </div>
      ) : null}

      <main className="layout">
        <section className="card composer">
          <h2>New habit</h2>
          <p className="hint">Keep the name small enough to finish on a bad day.</p>
          <div className="chips">
            {SUGGESTIONS.map((item) => (
              <button
                key={item.name}
                type="button"
                className="chip"
                onClick={() => {
                  setName(item.name);
                  setDescription(item.description);
                }}
              >
                {item.name}
              </button>
            ))}
          </div>
          <form onSubmit={onCreate}>
            {formError ? <p className="error">{formError}</p> : null}
            <label htmlFor="habit-name">Name</label>
            <input
              id="habit-name"
              value={name}
              maxLength={120}
              required
              onChange={(event) => setName(event.target.value)}
            />
            <label htmlFor="habit-description">Intention</label>
            <textarea
              id="habit-description"
              value={description}
              maxLength={500}
              placeholder="Optional. What does done look like?"
              onChange={(event) => setDescription(event.target.value)}
            />
            <button className="primary" type="submit" disabled={pending === "create"}>
              {pending === "create" ? "Saving…" : "Start tracking"}
            </button>
          </form>
        </section>

        <section className={selected ? "board with-detail" : "board"}>
          <div className="card list">
            <h2>Habits</h2>
            {loading ? <p className="hint">Loading habits…</p> : null}
            {!loading && habits.length === 0 ? (
              <p className="empty">No habits yet. Add one, then log a few days to grow a streak.</p>
            ) : null}
            <div className="habit-list">
              {habits.map((habit) => (
                <article
                  key={habit.id}
                  className={habit.id === selectedId ? "habit active" : "habit"}
                >
                  <button type="button" className="habit-open" onClick={() => openHabit(habit.id)}>
                    <span>
                      <span className="habit-name">{habit.name}</span>
                      <span className="habit-meta">
                        Longest {habit.longest_streak} · {habit.total_checkins} check-ins
                      </span>
                    </span>
                    <span className="habit-count">
                      <strong>{habit.current_streak}</strong>
                      <span>current</span>
                    </span>
                  </button>
                  <button
                    type="button"
                    className="tiny"
                    disabled={habit.checked_in_on || pending === `today-${habit.id}`}
                    onClick={() => logToday(habit.id)}
                  >
                    {habit.checked_in_on ? "Logged today" : "Log today"}
                  </button>
                </article>
              ))}
            </div>
          </div>

          {selected ? (
            <article className="card detail">
              <header className="detail-head">
                <div>
                  <p className="eyebrow">Selected habit</p>
                  <h2>{selected.name}</h2>
                  {selected.description ? <p className="hint">{selected.description}</p> : null}
                </div>
                <button type="button" className="danger" onClick={onDelete} disabled={pending === "delete"}>
                  {confirmDelete ? "Confirm remove" : "Remove"}
                </button>
              </header>

              {detailError ? <p className="error">{detailError}</p> : null}

              {!statsMatch ? <p className="hint">Counting streaks…</p> : null}

              {statsMatch ? (
                <>
                  <div className="stats">
                    <p className="stat current">
                      <strong>{statsMatch.current_streak}</strong>
                      <span>Current streak</span>
                    </p>
                    <p className="stat">
                      <strong>{statsMatch.longest_streak}</strong>
                      <span>Longest streak</span>
                    </p>
                    <p className="stat">
                      <strong>{statsMatch.total_checkins}</strong>
                      <span>Check-ins</span>
                    </p>
                  </div>
                  <p className="hint rule">
                    Current stays alive through today and yesterday. Two missed days reset it to
                    zero. Longest is the best run in the whole history.
                  </p>

                  <h3>Last 21 days</h3>
                  <div className="days">
                    {buildDays(asOf, statsMatch.checkins).map((day) => (
                      <button
                        key={day.key}
                        type="button"
                        className={day.checked ? "day on" : "day"}
                        data-today={day.today ? "true" : "false"}
                        title={`${prettyDate(day.key)}${day.checked ? " · logged" : ""}`}
                        onClick={() => setCheckDate(day.key)}
                      >
                        <span>{day.weekday}</span>
                        {day.day}
                      </button>
                    ))}
                  </div>

                  <div className="actions">
                    <button type="button" className="ghost" onClick={logRecentRun} disabled={pending === "run"}>
                      {pending === "run" ? "Logging…" : "Log the last 5 days"}
                    </button>
                  </div>

                  <h3>Streaks</h3>
                  {statsMatch.streaks.length === 0 ? (
                    <p className="hint">No check-ins yet.</p>
                  ) : (
                    <ul className="runs">
                      {statsMatch.streaks.map((streak) => (
                        <li key={`${streak.start_date}-${streak.end_date}`}>
                          <div className="bar">
                            <span
                              className={streak.active ? "live" : ""}
                              style={{ width: `${Math.max(8, (streak.length / longest) * 100)}%` }}
                            />
                          </div>
                          <p>
                            <strong>
                              {streak.length} {streak.length === 1 ? "day" : "days"}
                            </strong>
                            <span>
                              {streak.start_date === streak.end_date
                                ? prettyDate(streak.start_date)
                                : `${prettyDate(streak.start_date)} – ${prettyDate(streak.end_date)}`}
                            </span>
                            {streak.active ? <em>current</em> : null}
                          </p>
                        </li>
                      ))}
                    </ul>
                  )}

                  <h3>Log a day</h3>
                  <form className="checkin" onSubmit={onCheckin}>
                    <label htmlFor="check-date">Date</label>
                    <input
                      id="check-date"
                      type="date"
                      min="2000-01-01"
                      max={asOf}
                      value={checkDate}
                      onChange={(event) => setCheckDate(event.target.value)}
                      required
                    />
                    <label htmlFor="check-note">Note</label>
                    <input
                      id="check-note"
                      value={note}
                      maxLength={280}
                      placeholder="Optional"
                      onChange={(event) => setNote(event.target.value)}
                    />
                    <button className="primary" type="submit" disabled={pending === "checkin" || loggedOnFormDate}>
                      {loggedOnFormDate ? "Already logged" : pending === "checkin" ? "Saving…" : "Log check-in"}
                    </button>
                  </form>

                  <h3>Recent check-ins</h3>
                  {statsMatch.checkins.length === 0 ? (
                    <p className="hint">The ledger is empty.</p>
                  ) : (
                    <ul className="log">
                      {statsMatch.checkins.slice(0, 12).map((checkin) => (
                        <li key={checkin.id}>
                          <time dateTime={checkin.checked_on}>{prettyDate(checkin.checked_on)}</time>
                          <span>{checkin.note || "No note"}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              ) : null}
            </article>
          ) : null}
        </section>
      </main>

      <footer>
        <code>POST /habits</code>
        <code>POST /habits/{"{id}"}/checkins</code>
        <code>GET /habits/{"{id}"}/stats</code>
      </footer>
    </div>
  );
}
