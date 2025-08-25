# FT Daily Pipeline — Base Config & DB (Mongo)

Cette partie prépare la **configuration** et les **helpers MongoDB** (schema-less) pour un pipeline d’analyse d’articles (liens, articles, analyses LLM).  
Pas de `$jsonSchema` imposé — on garde la flexibilité, avec des **index** et des **upserts** idempotents.

## Arborescence (extrait)
Prject_analyse_news/
├─ app/
│ ├─ init.py
│ ├─ config.py # charge .env (Mongo URI, DB, noms de collections, UA…)
│ ├─ Database/
│ │ ├─ init.py
│ │ └─ db.py # connexion Mongo, index, upsert_link / upsert_article / upsert_analysis
│ └─ test/
│ ├─ init.py
│ └─ test_db.py # smoke test d’insertion/lecture
├─ requirements.txt
├─ .env.example # gabarit des variables d’env
├─ .gitignore
└─ README.md


## Prérequis
- Python 3.10+
- MongoDB local ou Atlas (URI)
- PowerShell / Bash

## Installation rapide (Windows PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=ft_daily
MONGODB_LINKS_COLLECTION=ft_links
MONGODB_ARTICLES_COLLECTION=ft_articles
MONGODB_ANALYSES_COLLECTION=ft_analyses
SCRAPER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36
GOOGLE_API_KEY=YOUR_API_KEY   # optionnel (pour la suite LLM)
```
## Lancer le smoke test
``` 
--Depuis la racine du projet: 

python -m app.test.test_db

--Sortie attendue (exemple) :

Links:     [ {...} ]
Articles:  [ {...} ]
Analyses:  [ {...} ]
