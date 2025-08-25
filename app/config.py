from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "ft_daily")
COLL_LINKS = os.getenv("MONGODB_LINKS_COLLECTION", "ft_links")
COLL_ARTICLES = os.getenv("MONGODB_ARTICLES_COLLECTION", "ft_articles")
COLL_ANALYSES = os.getenv("MONGODB_ANALYSES_COLLECTION", "ft_analyses")

# Réseau
SCRAPER_UA = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

GOOGLE_API_KEY = os.getenv("AIzaSyDw9wI1vkVGWJJShZTx6Y27Doc4Yzc0pUU")
