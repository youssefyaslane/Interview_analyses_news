# FT Daily Pipeline — Config, DB & Scraper (Mongo + SeleniumBase)

Ce projet met en place un pipeline d’analyse d’articles FT (liens, contenus, analyses LLM). 

---

## 📂 Arborescence (extrait)
```
Prject_analyse_news/
├─ app/
│  ├─ __init__.py
│  ├─ config.py 
│  ├─ main.py                  # Pipeline d’analyse d’articles
│  ├─ Database/
│  │   ├─ __init__.py
│  │   └─ db.py                 # connexion Mongo, index, upsert_link / upsert_article / upsert_analysis
│  ├─ scraping/
│  │   ├─ scrape_links.py       # scraper SeleniumBase → Mongo (ft_links)
│  │   ├─ fetch_articles.py  # scraper SeleniumBase → Mongo (ft_articles)
│  │   └─ utils.py              # utilitaires scraping (scroll, cookies, clean text)
│  ├─ analysis/
│  │   └─ analyze_with_Gemini.py   # Étape 4: LangChain + Gemini → ft_analyses
│  └─ test/
│     ├─ __init__.py
│     └─ test_db.py             # smoke test d’insertion/lecture
├─ requirements.txt
├─ .env.example                 # gabarit des variables d’env
├─ .gitignore
└─ README.md
```

---

## ⚙️ Prérequis
- Python 3.10+
- MongoDB local ou Atlas (URI)
- Chrome/Chromium installé (SeleniumBase s’en sert)
- (optionnel) Profil Chrome avec extension chargée (voir README précédent pour détails)

---

## 🚀 Installation rapide 
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Ajoute ensuite ce contenu dans **.env** :
```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=ft_daily
MONGODB_LINKS_COLLECTION=ft_links
MONGODB_ARTICLES_COLLECTION=ft_articles
MONGODB_ANALYSES_COLLECTION=ft_analyses

SCRAPER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36

# LLM (Étape 4)
GOOGLE_API_KEY=YOUR_API_KEY
LLM_MODEL=gemini-1.5-flash
```

---

## ▶️ Lancer les tests & scrapers

### 1. Tester la DB
```bash
python -m app.test.test_db
```

### 2. Scraper les liens publics FT → `ft_links`
```bash
python -m app.scraping.scrape_links
```
Exemple de sortie :
```
=== https://www.ft.com/ ===
[INFO] https://www.ft.com/ -> 30 liens trouvés
[OK] 30 liens upsertés pour https://www.ft.com/
...
✅ Terminé. Total liens upsertés: 121
```

### 3. Scraper les articles complets FT → `ft_articles`
```bash
python -m app.scraping.fetch_articles
```
Exemple de document inséré dans **ft_articles** :
```json
{
  "url": "https://www.ft.com/content/xxxx",
  "title": "Titre complet",
  "body_article": "Tout le texte intégral de l’article",
  "word_count": 1420,
  "fetched_at": "2025-08-27T12:30:00Z"
}
```

---

## 🔎 Étape 4 — Analyse LLM (LangChain + Gemini) → `ft_analyses`

### Lancer l’analyse
```bash
python -m app.analysis.analyze_with_langchain
```
- Sélectionne les articles **non encore analysés** (body_article non vide)
- Envoie à Gemini via **LangChain**
- Sauvegarde dans `ft_analyses` (**sans** `risks_or_implications`)

**Exemple de document `ft_analyses` :**
```json
{
  "url": "https://www.ft.com/content/xxxx",
  "model": "gemini-1.5-flash",
  "title_src": "Titre de l'article",
  "summary": "Résumé concis ...",
  "top_topics": ["semiconductors", "US policy", "Intel"],
  "sentiment": "neutral",
  "entities": [{"type":"ORG","name":"Intel"}],
  "analyzed_at": "2025-08-27T13:10:00Z"
}
```
---
## 📊 Utilisation dans Power BI / Excel

- Power BI Desktop → **Obtenir des données** → Excel → `data/articles_entities_dashboard.xlsx`
- Visuels conseillés :
  - Cartes KPI : *Total Articles*, *Avg Sentiment*, *Total Words*
  - Courbe : articles par jour (`ByDay`)
  - Barres : top entités (`Entities`) / par section (`BySection`)
  - Anneau : répartition par `sentiment_label`
  - Treemap ou nuage de mots : `Topics`
  - Graphe réseau (visuel custom) : `Cooccurrence`

### 📸 Dashboar
<img src="assets/img/dashbord_img.png" alt="FT Dashboard" width="1000"/>

---
## 📌 Roadmap
1. ✅ Step 1 : Config + DB helpers  
2. ✅ Step 2 : Scraper liens publics → `ft_links`  
3. ✅ Step 3 : Fetch articles complets → `ft_articles`  
4. ✅ Step 4 : Analyse LLM (LangChain + Gemini) → `ft_analyses`  
5. 🔜 Step 5 : Orchestration Airflow (1 exécution/jour)  
6. ✅ Step 6 : Dashboard (Metabase / PowerBI)

---

## ✨ Auteur
**Youssef Yaslane** — *Data Scientist | Big Data & IA Engineer*
