from app.Database.db import upsert_link, upsert_article, upsert_analysis, collections

def run():
    url = "https://www.ft.com/content/aec7bdce-d9ca-4416-a1b4-a0da5d11c715"

    upsert_link({
        "title": "US to take 10% stake in troubled chipmaker Intel",
        "url": url,
        "section": "home"
    })

    upsert_article({
        "url": url,
        "title": "US to take 10% stake in troubled chipmaker Intel",
        "preview": "Michael Acton in San Francisco ...",
        "paragraphs": ["First paragraph ...", "Second paragraph ..."],
        "published": "2025-08-22T10:03:00Z",
        "section": "home",
        "status": "ok"
    })

    upsert_analysis({
        "url": url,
        "model": "gemini-1.5-flash",
        "title_src": "US to take 10% stake in troubled chipmaker Intel",
        "summary": "Concise summary here.",
        "top_topics": ["semiconductors", "US policy", "Intel"],
        "sentiment": "neutral",
        "entities": [{"type": "ORG", "name": "Intel"}],
        "risks_or_implications": ["Policy uncertainty ..."]
    })

    links, articles, analyses = collections()
    print("Links:", list(links.find({}, {"_id": 0})))
    print("Articles:", list(articles.find({}, {"_id": 0})))
    print("Analyses:", list(analyses.find({}, {"_id": 0})))

if __name__ == "__main__":
    run()
