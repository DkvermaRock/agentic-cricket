from __future__ import annotations

import base64
import binascii
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import unicodedata
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from .game import RULES, ATTRIBUTES, cost, play_over, train, evaluate, lessons
from .store import Store

ROOT = Path(__file__).resolve().parent.parent


def now(): return datetime.now(timezone.utc).isoformat()


def normalize(raw):
    name = " ".join(unicodedata.normalize("NFKC", raw).split())
    if not 3 <= len(name) <= 24 or not any(unicodedata.category(c).startswith("L") for c in name) or not all(unicodedata.category(c)[0] in "LNM" or c in " '-." for c in name):
        raise HTTPException(422, "Use 3–24 characters: letters, numbers, spaces, apostrophes, periods or hyphens.")
    return name, unicodedata.normalize("NFKC", name.casefold())


class PlayerInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    power: int = Field(ge=10, le=95, strict=True)
    timing: int = Field(ge=10, le=95, strict=True)
    composure: int = Field(ge=10, le=95, strict=True)


class MatchInput(BaseModel):
    seed: int | None = Field(default=None, ge=0, le=2**31-1, strict=True)
    target: int = Field(default=12, ge=6, le=24, strict=True)


def public(row):
    p = dict(row)
    p["lessons"] = lessons(json.loads(p.pop("policy")))
    p.pop("practice"); p.pop("name_key")
    p["training_remaining"] = 6000 - p["training_balls"]
    return p


def create_app(database=None):
    @asynccontextmanager
    async def lifespan(app):
        yield
        app.state.store.engine.dispose()

    app = FastAPI(title="Boundary — Agent Arena", version="0.2.0", lifespan=lifespan)
    password = os.environ.get("CRICKET_DEMO_PASSWORD", "")
    hosted = os.environ.get("RENDER") == "true" or os.environ.get("CRICKET_REQUIRE_AUTH") == "true"
    if hosted and len(password) < 16:
        raise ValueError("Hosted mode requires CRICKET_DEMO_PASSWORD (16+ characters).")
    if os.environ.get("RENDER") == "true" and database is None and not os.environ.get("DATABASE_URL"):
        raise ValueError("Render requires DATABASE_URL for persistent player data.")
    if password:
        username = os.environ.get("CRICKET_DEMO_USERNAME", "cricket")
        @app.middleware("http")
        async def authenticate(request, call_next):
            if request.url.path == "/api/health": return await call_next(request)
            try:
                scheme, encoded = request.headers.get("authorization", "").split(" ", 1)
                u, p = base64.b64decode(encoded, validate=True).decode().split(":", 1)
                valid = scheme.lower() == "basic" and (secrets.compare_digest(u.encode(), username.encode()) & secrets.compare_digest(p.encode(), password.encode()))
            except (ValueError, binascii.Error, UnicodeDecodeError): valid = False
            if not valid:
                return JSONResponse({"detail": "Sign in to the private arena."}, 401, headers={"WWW-Authenticate": 'Basic realm="Boundary", charset="UTF-8"', "Cache-Control": "no-store"})
            return await call_next(request)

    store = Store(database or os.environ.get("DATABASE_URL") or os.environ.get("CRICKET_DB_PATH", ROOT / "data" / "arena.sqlite3"))
    app.state.store = store

    def require(id):
        with store.connection() as db:
            row = db.execute(text("SELECT * FROM players WHERE id=:id"), {"id": id}).mappings().first()
        if row is None: raise HTTPException(404, "Player not found.")
        return row

    @app.get("/api/health")
    def health():
        with store.connection() as db: db.execute(text("SELECT 1"))
        return {"status": "ok", "rules_version": RULES}

    @app.get("/api/meta")
    def meta():
        with store.connection() as db: coins = db.execute(text("SELECT coins FROM club WHERE id=1")).scalar_one()
        return {"coins": coins, "training_allowance": 6000, "training_batch": 2000, "rules_version": RULES}

    @app.get("/api/exhibition")
    def exhibition():
        player = {"id": "exhibition", "name": "Aarav Vale", "power": 74, "timing": 72, "composure": 68, "version": 0, "training_balls": 0, "lessons": []}
        match = play_over(player, {}, 100, 18)
        return {"player": player, "match": {**match, "id": "exhibition-100", "player_id": player["id"], "player_name": player["name"], "policy_version": 0, "exhibition": True}}

    @app.get("/api/players")
    def players():
        with store.connection() as db:
            return [public(r) for r in db.execute(text("SELECT * FROM players ORDER BY created_at")).mappings()]

    @app.post("/api/players", status_code=201)
    def create(body: PlayerInput):
        name, key = normalize(body.name)
        values = {**body.model_dump(), "id": str(uuid.uuid4()), "name": name, "key": key, "cost": cost(body.model_dump()), "created_at": now()}
        try:
            with store.transaction() as db:
                db.execute(text("INSERT INTO players (id,name,name_key,power,timing,composure,cost,created_at) VALUES (:id,:name,:key,:power,:timing,:composure,:cost,:created_at)"), values)
                if db.execute(text("UPDATE club SET coins=coins-:cost WHERE id=1 AND coins>=:cost"), values).rowcount != 1:
                    raise HTTPException(409, "Not enough coins. Lower the attributes to reduce the cost.")
        except IntegrityError as exc:
            if "players.name_key" in str(exc.orig) or getattr(getattr(exc.orig, "diag", None), "constraint_name", None) == "players_name_key_key":
                raise HTTPException(409, "That player name is already taken. Choose a unique name.") from exc
            raise
        return public(require(values["id"]))

    @app.post("/api/players/{id}/train")
    def practice(id: str):
        player = dict(require(id))
        if player["training_balls"] >= 6000: raise HTTPException(409, "This player's 6,000-ball practice allowance is used.")
        seed = secrets.randbelow(2**30)
        candidate = train(player, json.loads(player["practice"]), seed)
        report = evaluate(player, json.loads(player["policy"]), candidate, seed + 2**30)
        version = player["version"] + int(report["accepted"])
        report.update({"id": str(uuid.uuid4()), "player_id": id, "created_at": now(), "training_seed": seed, "training_balls": 2000, "policy_version": version})
        with store.transaction() as db:
            result = db.execute(text("UPDATE players SET policy=:policy,practice=:practice,training_balls=training_balls+2000,version=:version WHERE id=:id AND training_balls=:previous"), {"policy": json.dumps(candidate) if report["accepted"] else player["policy"], "practice": json.dumps(candidate), "version": version, "id": id, "previous": player["training_balls"]})
            if result.rowcount != 1: raise HTTPException(409, "Another practice session finished first. Refresh the player.")
            db.execute(text("INSERT INTO reports VALUES (:id,:player,:payload,:created_at)"), {"id": report["id"], "player": id, "payload": json.dumps(report), "created_at": report["created_at"]})
        return {"player": public(require(id)), "report": report}

    @app.get("/api/players/{id}/reports")
    def reports(id: str):
        require(id)
        with store.connection() as db:
            return [json.loads(r[0]) for r in db.execute(text("SELECT payload FROM reports WHERE player_id=:id ORDER BY created_at DESC"), {"id": id})]

    @app.post("/api/players/{id}/matches", status_code=201)
    def play(id: str, body: MatchInput):
        player = dict(require(id))
        result = play_over(player, json.loads(player["policy"]), body.seed if body.seed is not None else secrets.randbelow(2**31), body.target)
        result.update({"id": str(uuid.uuid4()), "player_id": id, "player_name": player["name"], "policy_version": player["version"], "created_at": now(), "exhibition": False})
        with store.transaction() as db:
            db.execute(text("INSERT INTO matches VALUES (:id,:player,:payload,:created_at)"), {"id": result["id"], "player": id, "payload": json.dumps(result), "created_at": result["created_at"]})
        return result

    @app.get("/api/players/{id}/matches")
    def matches(id: str):
        require(id)
        with store.connection() as db:
            return [json.loads(r[0]) for r in db.execute(text("SELECT payload FROM matches WHERE player_id=:id ORDER BY created_at DESC LIMIT 10"), {"id": id})]

    dist = ROOT / "frontend" / "dist"
    if dist.is_dir(): app.mount("/", StaticFiles(directory=dist, html=True), name="web")
    return app


app = create_app()
