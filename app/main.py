from app.scraping.scrape_links import scrape_and_store_links
from app.scraping.fetch_articles import fetch_articles_from_mongo
from app.analysis_llm.analyze_with_Gemini import analyze_batch_langchain


def main():

    profile_dir = r"C:\Users\HP\AppData\Local\Google\Chrome\User Data\Default"
    
    print("\n=== Étape 1/3 : Scraper liens publics (ft_links) ===")
    # Si ta fonction accepte un paramètre de limite, tu peux l’ajouter ici.
    scrape_and_store_links(limit_per_section=1)  # ex: scrape_and_store_links(limit_per_section=None)

    print("\n=== Étape 2/3 : Récupérer articles complets (ft_articles) ===")
    # None => traite toutes les URLs manquantes ; headless=True pour run silencieux
    fetch_articles_from_mongo(limit_per_run=5, headless=True, profile_dir=profile_dir)

    print("\n=== Étape 3/3 : Analyse LLM (ft_analyses) ===")
    # Choisis un batch raisonnable (ex: 60) ou None pour tout analyser
    analyze_batch_langchain(limit=5)

    print("\n✅ Pipeline terminé avec succès.")


if __name__ == "__main__":
    main()
