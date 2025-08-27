from __future__ import annotations
import os
from typing import List, Dict, Any, Optional
from time import sleep

from pydantic import BaseModel, Field
from pymongo import ASCENDING

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import LLM_MODEL, GOOGLE_API_KEY


from app.Database.db import collections, upsert_analysis

# -------- Config --------
MODEL_NAME = LLM_MODEL
GOOGLE_API_KEY = GOOGLE_API_KEY


# -------- Schéma de sortie (Pydantic) --------
class Entity(BaseModel):
    type: str = Field(description="Type d'entité: ORG | PERSON | LOC | OTHER")
    name: str = Field(description="Nom de l'entité")

class AnalysisOut(BaseModel):
    summary: str = Field(description="Résumé concis de l'article en 6-10 lignes.")
    top_topics: List[str] = Field(description="3 à 6 mots-clés majeurs (courts).")
    sentiment: str = Field(description="positive | neutral | negative")
    entities: List[Entity] = Field(default_factory=list, description="Entités importantes")

parser = JsonOutputParser(pydantic_object=AnalysisOut)

SYSTEM = (
    "Tu es un analyste de news financières. Résume l’article en 6-10 lignes, "
    "puis liste 3-6 sujets clés (mots courts), un sentiment global "
    "(positive/neutral/negative), et quelques entités importantes (ORG/PERSON/LOC). "
    "Réponds STRICTEMENT au format JSON demandé."
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM),
        MessagesPlaceholder("format_instructions"),
        ("human",
         "TITRE:\n{title}\n\n"
         "ARTICLE:\n{body}\n")
    ]
)

# Format instructions injectées
format_instructions = [
    ("system", parser.get_format_instructions())
]

# Modèle Gemini via LangChain
llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    api_key=GOOGLE_API_KEY,
    temperature=0.2,
    max_output_tokens=2048,
)

# Chaîne LCEL
chain = prompt | llm | parser

# -------- Sélection des articles à analyser --------
def _pick_unanalyzed(limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    _, articles, analyses = collections()
    already = {a["url"] for a in analyses.find({}, {"url": 1})}

    cur = articles.find(
        {"body_article": {"$exists": True, "$ne": ""}},
        {"url": 1, "title": 1, "body_article": 1}
    ).sort("fetched_at", ASCENDING)

    picked: List[Dict[str, Any]] = []
    for doc in cur:
        if doc["url"] not in already:
            picked.append(doc)
            if isinstance(limit, int) and limit > 0 and len(picked) >= limit:
                break
    return picked

# -------- Run batch --------
def analyze_batch_langchain(limit: Optional[int] = 100, delay_s: float = 0.6) -> None:
    batch = _pick_unanalyzed(limit=limit)
    if not batch:
        print("[INFO] Rien à analyser (ft_articles déjà couverts ou vides).")
        return

    print(f"[INFO] {len(batch)} article(s) à analyser avec LangChain/{MODEL_NAME}…")
    ok = err = 0

    for i, doc in enumerate(batch, 1):
        url = doc["url"]
        title = (doc.get("title") or "").strip()
        body = (doc.get("body_article") or "").strip()
        print(f"\n[{i}/{len(batch)}] {url}")

        try:
            result: AnalysisOut = chain.invoke(
                {
                    "title": title,
                    "body": body,
                    "format_instructions": format_instructions,
                }
            )
            upsert_analysis({
                "url": url,
                "model": MODEL_NAME,
                "title_src": title,
                "summary": result["summary"],
                "top_topics": result.get("top_topics", []),
                "sentiment": result.get("sentiment", "neutral"),
                "entities": result.get("entities", []),
            })
            print("  -> OK")
            ok += 1
        except Exception as e:
            print("  -> ERROR:", type(e).__name__, e)
            err += 1

        sleep(delay_s)

    print(f"\n✅ Terminé. {ok} OK, {err} erreurs.")

if __name__ == "__main__":
    analyze_batch_langchain(limit=100)
