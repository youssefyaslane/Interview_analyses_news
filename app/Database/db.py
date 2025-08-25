from datetime import datetime
from typing import Tuple
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection

from app.config import (
    MONGODB_URI, MONGODB_DB,
    COLL_LINKS, COLL_ARTICLES, COLL_ANALYSES
)

_client = None  # singleton client


def get_client() -> MongoClient:
    """Retourne un MongoClient réutilisable."""
    global _client
    if _client is None:
        _client = MongoClient(
            MONGODB_URI,
            connectTimeoutMS=20_000,
            serverSelectionTimeoutMS=20_000,
            socketTimeoutMS=20_000,
        )
    return _client


def get_db():
    """Retourne la base Mongo."""
    return get_client()[MONGODB_DB]


def collections() -> Tuple[Collection, Collection, Collection]:
    """
    Retourne (links, articles, analyses) et s'assure des index.
    Pas de $jsonSchema : Mongo reste schema-less.
    """
    db = get_db()
    links = db[COLL_LINKS]
    articles = db[COLL_ARTICLES]
    analyses = db[COLL_ANALYSES]

    # Index & unicité
    links.create_index([("url", ASCENDING)], unique=True)
    links.create_index([("section", ASCENDING)])
    links.create_index([("first_seen", ASCENDING)])
    links.create_index([("last_seen", ASCENDING)])

    articles.create_index([("url", ASCENDING)], unique=True)
    articles.create_index([("fetched_at", ASCENDING)])
    articles.create_index([("section", ASCENDING)])
    articles.create_index([("status", ASCENDING)])

    analyses.create_index([("url", ASCENDING)], unique=True)
    analyses.create_index([("analyzed_at", ASCENDING)])
    analyses.create_index([("sentiment", ASCENDING)])
    analyses.create_index([("top_topics", ASCENDING)])  # multikey

    return links, articles, analyses


# -------------------- UPSERTS --------------------

def upsert_link(doc: dict) -> None:
    """
    Upsert d’un lien (issu du listing).
    Attendu min:
      {"title": "...", "url": "https://...", "section": "home"}
    Champs auto:
      source (default 'listing'), first_seen (à l'insertion), last_seen (toutes MAJ)
    """
    links, _, _ = collections()
    now = datetime.utcnow()
    payload = {
        "title": (doc.get("title") or "").strip(),
        "section": doc.get("section", "home"),
        "source": doc.get("source", "listing"),
        "last_seen": now,
    }
    links.update_one(
        {"url": doc["url"]},
        {"$setOnInsert": {"first_seen": now}, "$set": payload},
        upsert=True,
    )


def _compute_word_count(paragraphs) -> int:
    if not paragraphs:
        return 0
    return sum(len((p or "").split()) for p in paragraphs if isinstance(p, str))


def upsert_article(doc: dict) -> None:
    """
    Upsert d’un article parsé.
    Attendu min:
      {"url": "...", "title": "...", "preview": "..."}
    Optionnels:
      paragraphs: list[str], published: str|null, section: str, status: "ok"/"empty_or_paywalled"/"error:..."
    Champs auto:
      word_count, fetched_at
    """
    _, articles, _ = collections()
    paragraphs = doc.get("paragraphs") or []
    payload = {
        "url": doc["url"],
        "title": (doc.get("title") or "").strip(),
        "preview": (doc.get("preview") or "").strip(),
        "paragraphs": paragraphs if isinstance(paragraphs, list) else [],
        "published": doc.get("published"),
        "section": doc.get("section"),
        "status": doc.get("status", "unknown"),
        "word_count": _compute_word_count(paragraphs),
        "fetched_at": datetime.utcnow(),
    }
    articles.update_one({"url": payload["url"]}, {"$set": payload}, upsert=True)


def upsert_analysis(doc: dict) -> None:
    """
    Upsert d’une analyse LLM.
    Attendu min:
      {"url": "...", "summary": "...", "top_topics": [...], "sentiment": "..."}
    Optionnels:
      model, title_src, entities[], risks_or_implications[]
    Champs auto:
      analyzed_at
    """
    _, _, analyses = collections()
    payload = {
        "url": doc["url"],
        "model": doc.get("model", "gemini-1.5-flash"),
        "title_src": doc.get("title_src"),
        "summary": (doc.get("summary") or "").strip(),
        "top_topics": doc.get("top_topics") or [],
        "sentiment": doc.get("sentiment", "neutral"),
        "entities": doc.get("entities") or [],
        "risks_or_implications": doc.get("risks_or_implications") or [],
        "analyzed_at": datetime.utcnow(),
    }
    analyses.update_one({"url": payload["url"]}, {"$set": payload}, upsert=True)
