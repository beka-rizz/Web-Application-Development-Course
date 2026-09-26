# Almaty Time

A small web app that shows the current time in Almaty (`Asia/Almaty`, UTC+5).

## Requirements

- [Docker](https://docs.docker.com/get-docker/)

## Run

From this folder:

```bash
docker build -t almaty-time .
docker run --rm -p 3000:3000 almaty-time
```

Open [http://localhost:3000](http://localhost:3000).

Stop the container with `Ctrl+C`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `PORT` | `3000` | Port the app listens on inside the container |
| `TZ` | `Asia/Almaty` | Time zone used for the clock |
| `APP_TITLE` | `Almaty Time` | Page title |