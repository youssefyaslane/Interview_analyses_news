# export_entities_to_excel.py
import os
from datetime import datetime
from itertools import combinations
from typing import Dict, Any, List, Iterable

import pandas as pd
from pymongo import MongoClient

# ====== CONFIG ======
# Mets ton URI Mongo ici ou via variable d'env MONGO_URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "ft_daily")
COLL_ARTICLES = os.getenv("MONGO_COLL_ARTICLES", "ft_analyses")

OUT_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_XLSX = os.path.join(OUT_DIR, "articles_entities_dashboard.xlsx")
OUT_CSV  = os.path.join(OUT_DIR, "articles.csv")


# ---------- Utils ----------
def parse_iso(dt):
    if isinstance(dt, datetime):
        return dt
    if isinstance(dt, dict) and "$date" in dt:
        try:
            return datetime.fromisoformat(str(dt["$date"]).replace("Z", "+00:00"))
        except Exception:
            return pd.NaT
    if isinstance(dt, str):
        try:
            return datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return pd.NaT
    return pd.NaT


def sentiment_to_score(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().lower()
    if s in ("positive", "pos", "positif"):
        return 1.0
    if s in ("negative", "neg", "negatif"):
        return -1.0
    if s in ("neutral", "neutre"):
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def list_to_semicolon(val):
    if isinstance(val, list):
        return ";".join([str(x) for x in val])
    if val is None:
        return ""
    return str(val)


# ---------- Normalisation article ----------
def normalize_article(doc: Dict[str, Any]) -> Dict[str, Any]:
    url = doc.get("url", "")
    title = doc.get("title") or doc.get("title_src") or ""
    summary = doc.get("summary", "")
    model = doc.get("model", "")
    section = doc.get("section", "")
    source = doc.get("source", "FT")
    analyzed_at = parse_iso(doc.get("analyzed_at"))
    published_at = parse_iso(doc.get("published_at"))

    sentiment_label = str(doc.get("sentiment", "")).strip()
    sentiment_score = sentiment_to_score(doc.get("sentiment"))

    topics_raw = doc.get("top_topics", doc.get("topics", []))
    topics = list_to_semicolon(topics_raw)

    wc = doc.get("word_count", None)
    if wc is None:
        wc = len(summary.split()) if isinstance(summary, str) else 0

    entities = doc.get("entities", [])
    num_entities = len(entities) if isinstance(entities, list) else 0

    return {
        "url": url,
        "title": title,
        "summary": summary,
        "section": section,
        "source": source,
        "published_at": published_at,
        "analyzed_at": analyzed_at,
        "sentiment_label": sentiment_label,
        "sentiment_score": sentiment_score,
        "topics": topics,
        "word_count": int(wc) if wc is not None else 0,
        "model": model,
        "num_entities": num_entities,
    }


# ---------- Explosions ----------
def explode_entities(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    ents = doc.get("entities", [])
    if not isinstance(ents, list) or not ents:
        return []
    url = doc.get("url", "")
    title = doc.get("title") or doc.get("title_src") or ""
    analyzed_at = parse_iso(doc.get("analyzed_at"))
    rows = []
    for e in ents:
        etype = e.get("type", "")
        ename = e.get("name", "")
        if not ename:
            continue
        rows.append({
            "url": url,
            "title": title,
            "entity_type": etype,   # PERSON / ORG / LOC / ...
            "entity_name": ename,
            "analyzed_at": analyzed_at,
        })
    return rows


def explode_topics(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = doc.get("url", "")
    title = doc.get("title") or doc.get("title_src") or ""
    analyzed_at = parse_iso(doc.get("analyzed_at"))
    raw = doc.get("top_topics", doc.get("topics", []))
    if isinstance(raw, list):
        topics = [str(x) for x in raw if str(x).strip()]
    elif isinstance(raw, str):
        topics = [t.strip() for t in raw.split(";") if t.strip()]
    else:
        topics = []
    return [{"url": url, "title": title, "topic": t, "analyzed_at": analyzed_at} for t in topics]


def cooccurrence_pairs(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    from itertools import combinations
    names = [e.get("name") for e in entities if e.get("name")]
    uniq = sorted(set(names))
    pairs = []
    for a, b in combinations(uniq, 2):
        pairs.append({"source": a, "target": b, "weight": 1})
    return pairs


# ---------- Main ----------
def main():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    col = db[COLL_ARTICLES]

    docs = list(col.find({}))
    print(f"[INFO] Documents: {len(docs)}")

    # Articles
    df_articles = pd.DataFrame([normalize_article(d) for d in docs])

    # Entities
    ent_rows = []
    for d in docs:
        ent_rows.extend(explode_entities(d))
    df_entities = pd.DataFrame(ent_rows) if ent_rows else pd.DataFrame(columns=["url","title","entity_type","entity_name","analyzed_at"])

    # Topics
    top_rows = []
    for d in docs:
        top_rows.extend(explode_topics(d))
    df_topics = pd.DataFrame(top_rows) if top_rows else pd.DataFrame(columns=["url","title","topic","analyzed_at"])

    # Cooccurrence
    co_rows = []
    for d in docs:
        co_rows.extend(cooccurrence_pairs(d.get("entities", []) or []))
    df_co = pd.DataFrame(co_rows) if co_rows else pd.DataFrame(columns=["source","target","weight"])
    if not df_co.empty:
        df_co = df_co.groupby(["source","target"], as_index=False)["weight"].sum()

    # KPI
    total_articles = len(df_articles)
    avg_sentiment = round(df_articles["sentiment_score"].mean(), 3) if total_articles else 0.0
    total_words = int(df_articles["word_count"].sum()) if total_articles else 0
    df_kpi = pd.DataFrame({
        "metric": ["Total Articles", "Avg Sentiment", "Total Words"],
        "value": [total_articles, avg_sentiment, total_words],
    })

    # ByDay
    if not df_articles.empty:
        tmp = df_articles.copy()
        tmp["day"] = pd.to_datetime(tmp["published_at"]).dt.date
        df_byday = tmp.groupby("day", as_index=False).agg(
            articles=("url","count"),
            avg_sentiment=("sentiment_score","mean"),
            words=("word_count","sum"),
        )
    else:
        df_byday = pd.DataFrame(columns=["day","articles","avg_sentiment","words"])

    # BySection
    if not df_articles.empty:
        df_bysection = df_articles.groupby("section", as_index=False).agg(
            articles=("url","count"),
            avg_sentiment=("sentiment_score","mean"),
            words=("word_count","sum"),
        ).sort_values("articles", ascending=False)
    else:
        df_bysection = pd.DataFrame(columns=["section","articles","avg_sentiment","words"])

    # Sauvegarde CSV Articles (facile pour Power BI aussi)
    df_articles.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"[OK] CSV -> {OUT_CSV}")

    # Excel multi-feuilles
    with pd.ExcelWriter(OUT_XLSX, engine="xlsxwriter", datetime_format="yyyy-mm-dd hh:mm") as writer:
        df_articles.to_excel(writer, index=False, sheet_name="Articles")
        df_entities.to_excel(writer, index=False, sheet_name="Entities")
        df_topics.to_excel(writer, index=False, sheet_name="Topics")
        df_byday.to_excel(writer, index=False, sheet_name="ByDay")
        df_bysection.to_excel(writer, index=False, sheet_name="BySection")
        df_co.to_excel(writer, index=False, sheet_name="Cooccurrence")
        df_kpi.to_excel(writer, index=False, sheet_name="KPI")

        # Auto width
        for sheet, df in {
            "Articles": df_articles,
            "Entities": df_entities,
            "Topics": df_topics,
            "ByDay": df_byday,
            "BySection": df_bysection,
            "Cooccurrence": df_co,
            "KPI": df_kpi,
        }.items():
            ws = writer.sheets[sheet]
            if df is None or df.empty:
                ws.set_column(0, 20, 16)
                continue
            for i, col in enumerate(df.columns):
                try:
                    max_len = max(12, int(df[col].astype(str).str.len().max()))
                except Exception:
                    max_len = 16
                ws.set_column(i, i, min(max_len + 2, 80))

    print(f"[OK] Excel -> {OUT_XLSX}")


if __name__ == "__main__":
    main()
