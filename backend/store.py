from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL, make_url
from sqlalchemy.pool import NullPool

SCHEMA = """
CREATE TABLE IF NOT EXISTS club (id INTEGER PRIMARY KEY CHECK(id=1), coins INTEGER NOT NULL CHECK(coins>=0));
INSERT INTO club VALUES (1,100) ON CONFLICT(id) DO NOTHING;
CREATE TABLE IF NOT EXISTS players (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE,
 power INTEGER NOT NULL, timing INTEGER NOT NULL, composure INTEGER NOT NULL, cost INTEGER NOT NULL,
 policy TEXT NOT NULL DEFAULT '{}', practice TEXT NOT NULL DEFAULT '{}',
 training_balls INTEGER NOT NULL DEFAULT 0, version INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, player_id TEXT NOT NULL REFERENCES players(id), payload TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS matches (id TEXT PRIMARY KEY, player_id TEXT NOT NULL REFERENCES players(id), payload TEXT NOT NULL, created_at TEXT NOT NULL);
"""


class Store:
    def __init__(self, path):
        self.path = str(path)
        self.postgres = self.path.startswith(("postgres://", "postgresql://", "postgresql+psycopg://"))
        if self.postgres:
            url = make_url(self.path.replace("postgres://", "postgresql://", 1)).set(drivername="postgresql+psycopg")
            if url.host not in {"localhost", "127.0.0.1", "::1"} and url.query.get("sslmode") not in {"require", "verify-ca", "verify-full"}:
                raise ValueError("Remote DATABASE_URL requires sslmode=require or a verified TLS mode.")
            self.engine = create_engine(url, connect_args={"connect_timeout": 10, "prepare_threshold": None}, pool_size=3, max_overflow=2, pool_pre_ping=True, hide_parameters=True)
        else:
            if "://" in self.path:
                raise ValueError("DATABASE_URL must use PostgreSQL.")
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            self.engine = create_engine(URL.create("sqlite", database=self.path), connect_args={"timeout": 15, "check_same_thread": False}, poolclass=NullPool)
            @event.listens_for(self.engine, "connect")
            def configure(db, _):
                db.execute("PRAGMA foreign_keys=ON")
            with self.engine.connect() as db:
                db.exec_driver_sql("PRAGMA journal_mode=WAL")
        with self.engine.begin() as db:
            if self.postgres:
                db.exec_driver_sql("SELECT pg_advisory_xact_lock(746391052)")
            for sql in SCHEMA.split(";"):
                if sql.strip(): db.exec_driver_sql(sql)
            if self.postgres:
                for table in ("club", "players", "reports", "matches"):
                    db.exec_driver_sql(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    @contextmanager
    def connection(self):
        with self.engine.connect() as db:
            yield db

    @contextmanager
    def transaction(self):
        with self.engine.connect() as db:
            if not self.postgres: db.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
