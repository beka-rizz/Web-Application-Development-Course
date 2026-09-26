const http = require("http");

const port = Number(process.env.PORT) || 3000;
const timeZone = process.env.TZ || "Asia/Almaty";
const appTitle = process.env.APP_TITLE || "Almaty Time";

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function almatyTime(date) {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  }).format(date);
}

function page() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(appTitle)}</title>
</head>
<body>
  <h1>Current time in Almaty</h1>
  <p id="time">${escapeHtml(almatyTime(new Date()))}</p>
  <script>
    const timeZone = ${JSON.stringify(timeZone)};
    const timeEl = document.getElementById("time");

    function tick() {
      timeEl.textContent = new Intl.DateTimeFormat("en-GB", {
        timeZone,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hourCycle: "h23",
      }).format(new Date());
    }

    setInterval(tick, 1000);
  </script>
</body>
</html>`;
}

const server = http.createServer((req, res) => {
  const url = req.url === "/" ? "/" : req.url.split("?")[0];

  if (url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", timeZone }));
    return;
  }

  if (url !== "/") {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Not found");
    return;
  }

  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(page());
});

server.listen(port, "0.0.0.0", () => {
  console.log(`${appTitle} listening on 0.0.0.0:${port} (${timeZone})`);
});

function shutdown() {
  server.close(() => process.exit(0));
}

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
