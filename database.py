import os
import asyncpg

from config import DATABASE_URL

pool = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS vacancies (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidates (
    id              SERIAL PRIMARY KEY,
    telegram_id     BIGINT NOT NULL,
    username        TEXT,
    full_name       TEXT NOT NULL,
    phone           TEXT NOT NULL,
    experience      TEXT NOT NULL,
    resume_file_id  TEXT NOT NULL,
    resume_file_name TEXT,
    vacancy_title   TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_telegram_id ON candidates(telegram_id);
"""

async def init_db() -> None:
    global pool
    # connect to the database
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set.")
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute(_SCHEMA)

async def save_candidate(
    telegram_id: int,
    username: str | None,
    full_name: str,
    phone: str,
    experience: str,
    resume_file_id: str,
    resume_file_name: str | None,
    vacancy_title: str | None = None,
) -> int:
    async with pool.acquire() as conn:
        query = """
            INSERT INTO candidates
                (telegram_id, username, full_name, phone, experience, resume_file_id, resume_file_name, vacancy_title)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """
        row_id = await conn.fetchval(
            query,
            telegram_id, username, full_name, phone, experience, resume_file_id, resume_file_name, vacancy_title
        )
        return row_id

async def get_candidate(candidate_id: int) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM candidates WHERE id = $1", candidate_id)
        return dict(row) if row else None

async def list_candidates(limit: int = 50) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM candidates ORDER BY id DESC LIMIT $1", limit)
        return [dict(r) for r in rows]

async def get_candidates_count() -> int:
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM candidates")
        return count or 0

async def get_all_candidates() -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM candidates ORDER BY id ASC")
        return [dict(r) for r in rows]

async def get_candidates_by_vacancy(vacancy_title: str) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM candidates WHERE vacancy_title = $1 ORDER BY id ASC", vacancy_title)
        return [dict(r) for r in rows]

async def search_candidates(query: str) -> list[dict]:
    async with pool.acquire() as conn:
        search_pattern = f"%{query}%"
        rows = await conn.fetch(
            "SELECT * FROM candidates WHERE vacancy_title ILIKE $1 OR experience ILIKE $1 ORDER BY id ASC", 
            search_pattern
        )
        return [dict(r) for r in rows]

async def create_vacancy(title: str, description: str) -> int:
    async with pool.acquire() as conn:
        row_id = await conn.fetchval(
            "INSERT INTO vacancies (title, description) VALUES ($1, $2) RETURNING id",
            title, description
        )
        return row_id

async def get_active_vacancies() -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM vacancies WHERE is_active = TRUE ORDER BY id ASC")
        return [dict(r) for r in rows]

async def delete_vacancy(vacancy_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute("UPDATE vacancies SET is_active = FALSE WHERE id = $1", vacancy_id)
