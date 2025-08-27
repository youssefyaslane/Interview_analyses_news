# FT Daily Pipeline — Config, DB & Scraper (Mongo + SeleniumBase)

Ce projet met en place un pipeline d’analyse d’articles FT (liens, contenus, analyses LLM). 

---

## 📂 Arborescence (extrait)
```
Prject_analyse_news/
├─ app/
│  ├─ __init__.py
│  ├─ config.py                 # charge .env (Mongo URI, DB, noms de collections, UA…)
│  ├─ Database/
│  │   ├─ __init__.py
│  │   └─ db.py                 # connexion Mongo, index, upsert_link / upsert_article / upsert_analysis
│  ├─ scraping/
│  │   ├─ scrape_links.py       # scraper SeleniumBase → Mongo (ft_links)
│  │   ├─ fetch_articles_selenium.py  # scraper SeleniumBase → Mongo (ft_articles)
│  │   └─ utils.py              # utilitaires scraping (scroll, cookies, clean text)
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
- (optionnel) Profil Chrome avec extension chargée (voir plus bas)

---

## 🚀 Installation rapide (Windows PowerShell)
```
python -m venv venv
venv\Scripts\Activate.ps1
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
GOOGLE_API_KEY=YOUR_API_KEY   # optionnel (pour la suite LLM)
```

---

## ▶️ Lancer les tests & scrapers

### 1. Tester la DB
```bash
python -m app.test.test_db
```

### 2. Lancer la DB
```bash
python -m app.Database.db
```
**Sortie attendue (exemple) :**
```
Links:     [ {...} ]
Articles:  [ {...} ]
Analyses:  [ {...} ]
```

### 3. Scraper les liens publics FT
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

Les liens sont insérés/mis à jour dans la collection **ft_links** de MongoDB.

---

## 🧩 Utiliser Chrome avec extension

téléchargement d’extensions de contournement de paywall **profil Chrome avec extension** :

1. Télécharge ton dossier d'après ce lien "https://gitflic.ru/project/magnolia1234/bypass-paywalls-chrome-clean#installation".
2. Ouvre Chrome → `chrome://extensions/`.
3. Active **Mode développeur** (coin supérieur droit).
4. Clique sur **Charger l’extension non empaquetée**.
5. poser ton dossier.
6. Mets à jour `fetch_articles_selenium.py` pour réutiliser ton profil :
   ```python
   profile_dir = r"C:\Users\HP\AppData\Local\Google\Chrome\User Data\Default"
   fetch_articles_from_mongo(limit_per_run=None, headless=False, profile_dir=profile_dir)
   ```

---

### 4. Scraper les articles complets FT
```bash
python -m app.scraping.fetch_articles_selenium
```

### Collection `ft_links`
```json
{
  "title": "US to take 10% stake in troubled chipmaker Intel",
  "url": "https://www.ft.com/content/Id_article",
  "section": "home",
  "source": "listing",
  "first_seen": "2025-08-25T10:44:29Z",
  "last_seen": "2025-08-25T10:44:29Z"
}
```

### Collection `ft_articles`
```json
{
  "url": "https://www.ft.com/content/Id_article",
  "title": "US to take 10% stake in troubled chipmaker Intel",
  "body_article": "Texte complet de l’article...",
  "word_count": 1432,
  "fetched_at": "2025-08-27T11:12:00Z"
}
```

---

## 📌 Roadmap
1. ✅ Step 1 : Config + DB helpers  
2. ✅ Step 2 : Scraper liens publics → `ft_links`  
3. ✅ Step 3 : Fetch articles complets → `ft_articles`  
4. 🔜 Step 4 : Analyse LLM (Gemini) → `ft_analyses`  
5. 🔜 Step 5 : Orchestration Airflow (1 exécution/jour)  
6. 🔜 Step 6 : Dashboard (Metabase / PowerBI)

---
## ✨ Auteur
**Youssef Yaslane** — *Data Scientist | Big Data & IA Engineer*
