export function localISODate(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function addDays(isoDate, days) {
  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  date.setDate(date.getDate() + days);
  return localISODate(date);
}

export function prettyDate(isoDate) {
  if (!isoDate) return "";
  const [year, month, day] = isoDate.slice(0, 10).split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

export function buildDays(asOf, checkins, count = 21) {
  const logged = new Set(checkins.map((checkin) => checkin.checked_on));
  const days = [];
  for (let offset = count - 1; offset >= 0; offset -= 1) {
    const key = addDays(asOf, -offset);
    const [year, month, day] = key.split("-").map(Number);
    const date = new Date(year, month - 1, day);
    days.push({
      key,
      day,
      weekday: date.toLocaleDateString(undefined, { weekday: "narrow" }),
      checked: logged.has(key),
      today: key === asOf,
    });
  }
  return days;
}
