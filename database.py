from __future__ import annotations

import os
import socket
import json
import logging
from typing import Any
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

logger = logging.getLogger("ai_tutoring_engine.database")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "studytable_db")


def check_mongo_connection(uri: str) -> bool:
    try:
        host, port = "localhost", 27017
        if "://" in uri:
            parts = uri.split("://")[1].split("/")[0]
            if "@" in parts:
                parts = parts.split("@")[1]
            if ":" in parts:
                host, port_str = parts.split(":")
                port = int(port_str.split(",")[0])
            else:
                host = parts
        
        # Fast socket connection check
        s = socket.create_connection((host, port), timeout=0.3)
        s.close()
        return True
    except Exception:
        return False


class MockCollection:
    def __init__(self, filename: str):
        self.filename = filename
        self.data: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def save(self):
        try:
            with open(self.filename, "w") as f:
                json.dump(self.data, f, default=str, indent=2)
        except Exception as e:
            logger.error("Failed to save mock DB file %s: %s", self.filename, e)

    async def find_one(self, filter: dict[str, Any], projection: dict[str, Any] | None = None) -> dict[str, Any] | None:
        self.load()
        for doc in self.data.values():
            match = True
            for k, v in filter.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                res = dict(doc)
                if projection and "_id" in projection and projection["_id"] == 0:
                    res.pop("_id", None)
                return res
        return None

    async def insert_one(self, document: dict[str, Any]) -> None:
        self.load()
        doc_id = document.get("session_id") or document.get("question_id") or str(len(self.data))
        document["_id"] = doc_id
        self.data[doc_id] = document
        self.save()

    async def update_one(self, filter: dict[str, Any], update: dict[str, Any], upsert: bool = False) -> None:
        self.load()
        matched_id = None
        for doc_id, doc in self.data.items():
            match = True
            for k, v in filter.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                matched_id = doc_id
                break

        if not matched_id:
            if upsert:
                doc = dict(filter)
                matched_id = doc.get("question_id") or doc.get("session_id") or str(len(self.data))
                doc["_id"] = matched_id
                self.data[matched_id] = doc
            else:
                return

        doc = self.data[matched_id]
        
        # Apply updates
        if "$set" in update:
            for k, v in update["$set"].items():
                doc[k] = v

        if "$push" in update:
            for k, v in update["$push"].items():
                field = k
                val = v
                if isinstance(val, dict) and "$each" in val:
                    to_push = val["$each"]
                else:
                    to_push = [val]
                
                if field not in doc or not isinstance(doc[field], list):
                    doc[field] = []
                doc[field].extend(to_push)

        self.data[matched_id] = doc
        self.save()


class MockDatabase:
    def __init__(self):
        self.sessions = MockCollection("mock_sessions.json")
        self.question_library = MockCollection("mock_question_library.json")


# Determine if we should use MockDatabase or real MongoDB client
if check_mongo_connection(MONGO_URI):
    logger.info("MongoDB running on %s. Connecting with Motor...", MONGO_URI)
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
else:
    logger.warning("MongoDB NOT detected on %s. Falling back to local JSON database.", MONGO_URI)
    db = MockDatabase()
