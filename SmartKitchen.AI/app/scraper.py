from duckduckgo_search import DDGS
from recipe_scrapers import scrape_me
from typing import List, Dict
import random
import time

class WebRecipeScraper:
    def __init__(self):
        self.ddgs = DDGS()
        # Strictly only scrape these domains to ensure quality and scraper compatibility
        self.trusted_domains = [
            "allrecipes.com", "foodnetwork.com", "bbcgoodfood.com", "tasty.co",
            "bonappetit.com", "simplyrecipes.com", "delish.com", "thespruceeats.com",
            "epicurious.com", "food.com", "seriouseats.com", "yummly.com",
            "tasteofhome.com", "damndelicious.net", "sallysbakingaddiction.com",
            "loveandlemons.com", "minimalistbaker.com", "101cookbooks.com",
            "cookieandkate.com", "halfbakedharvest.com", "smittenkitchen.com",
            "budgetbytes.com", "inspiredtaste.net", "pinchofyum.com", "cooking.nytimes.com",
            "bettycrocker.com", "pillsbury.com", "kingarthurbaking.com", "marthastewart.com",
            "realsimple.com", "southernliving.com", "taste.com.au", "eatingwell.com"
        ]

    def search_and_scrape(self, ingredients: List[str], limit: int = 5) -> List[Dict]:
        """
        Search for recipes containing the ingredients and scrape their details.
        Implements cascading fallback to ensure results.
        """
        if not ingredients:
            return []
            
        results = []
        
        # Strategy:
        # 1. Prioritize Proteins
        priority_keywords = ["chicken", "beef", "steak", "pork", "fish", "salmon", "shrimp", "tuna", "egg", "eggs", "tofu", "meat"]
        sorted_ingredients = sorted(ingredients, key=lambda x: any(p in x.lower() for p in priority_keywords), reverse=True)
        
        # Search Attempts Configurations
        # We try strict first, then relax.
        attempts = []
        
        if len(sorted_ingredients) >= 4:
            attempts.append(sorted_ingredients[:4]) # Top 4
        if len(sorted_ingredients) >= 2:
            attempts.append(sorted_ingredients[:2]) # Top 2
        attempts.append([sorted_ingredients[0]])   # Top 1
        
        # Determine max results needed to fill the limit
        # We want to find 'limit' recipes.
        
        for search_set in attempts:
            if len(results) >= limit:
                break
                
            query = f"recipe using {', '.join(search_set)}"
            print(f"Web Scraping Query (Attempt): {query}")
            
            # Search
            candidate_urls = self._perform_search(query, max_res=40)
            
            # Filter matches
            valid_urls = [u for u in candidate_urls if any(d in u for d in self.trusted_domains)]
            print(f"Found {len(valid_urls)} valid URLs.")
            
            # Scrape
            for url in valid_urls:
                if len(results) >= limit:
                    break
                
                # Deduplicate: Don't scrape if we already have this url from a previous attempt
                if any(r['source_url'] == url for r in results):
                    continue
                    
                print(f"Scraping: {url}")
                try:
                    scraper = scrape_me(url)
                    if not scraper.title() or not scraper.ingredients() or not scraper.instructions_list():
                         continue
                         
                    recipe_data = {
                        "name": scraper.title(),
                        "rating": str(scraper.ratings() or "N/A"),
                        "prep_time": str(scraper.total_time() or "N/A"),
                        "cook_time": str(scraper.total_time() or "N/A"),
                        "total_time": str(scraper.total_time() or "N/A"),
                        "ingredients": [{"name": i, "quantity": "", "unit": ""} for i in scraper.ingredients()],
                        "directions": scraper.instructions_list(),
                        "image_url": scraper.image(),
                        "source_url": url
                    }
                    results.append(recipe_data)
                except Exception as e:
                    print(f"Failed to scrape {url}: {e}")
                    continue
                    
        return results

    def _perform_search(self, query: str, max_res: int) -> List[str]:
        try:
            # max_results arg
            search_results = list(self.ddgs.text(query, max_results=max_res))
            return [res['href'] for res in search_results if 'href' in res]
        except Exception as e:
            print(f"Search error for '{query}': {e}")
            return []

if __name__ == "__main__":
    s = WebRecipeScraper()
    print(s.search_and_scrape(["avocado", "toast"]))
