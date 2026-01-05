from app.scraper import WebRecipeScraper
s = WebRecipeScraper()
print(s.search_and_scrape(["bread", "eggs", "milk", "cinnamon"]))
