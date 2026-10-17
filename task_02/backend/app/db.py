import asyncio
import logging
import os

import aiomysql

log = logging.getLogger("streakline")

REQUIRED = ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")


def require_env():
    missing = [key for key in REQUIRED if not os.environ.get(key)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


async def connect_pool():
    last_error = None
    for attempt in range(1, 31):
        pool = None
        try:
            pool = await aiomysql.create_pool(
                host=os.environ["DB_HOST"],
                port=int(os.environ.get("DB_PORT", "3306")),
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
                db=os.environ["DB_NAME"],
                minsize=1,
                maxsize=10,
                autocommit=True,
                charset="utf8mb4",
            )
            async with pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute("SELECT 1")
            log.info("database connection ready")
            return pool
        except Exception as error:
            last_error = error
            if pool is not None:
                pool.close()
                await pool.wait_closed()
            log.info("waiting for database (%s/30)", attempt)
            if attempt == 30:
                break
            await asyncio.sleep(2)
    raise last_error


async def fetch_all(pool, sql, args=()):
    async with pool.acquire() as connection:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql, args)
            return await cursor.fetchall()


async def execute(pool, sql, args=()):
    async with pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(sql, args)
            return cursor.lastrowid, cursor.rowcount
