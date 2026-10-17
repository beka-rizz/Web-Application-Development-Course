async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (response.status === 204) return null;

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.error || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return data;
}

export function fetchHabits(asOf) {
  return request(`/habits?as_of=${encodeURIComponent(asOf)}`);
}

export function fetchStats(id, asOf) {
  return request(`/habits/${id}/stats?as_of=${encodeURIComponent(asOf)}`);
}

export function createHabit(body) {
  return request("/habits", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function createCheckin(id, body) {
  return request(`/habits/${id}/checkins`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function deleteHabit(id) {
  return request(`/habits/${id}`, { method: "DELETE" });
}
