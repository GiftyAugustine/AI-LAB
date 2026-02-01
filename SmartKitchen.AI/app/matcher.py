import json
import os
import random

class RecipeMatcher:
    def __init__(self, layer1_path: str, layer2_path: str = None):
        self.layer1_path = layer1_path
        self.layer2_path = layer2_path
        self.recipes = []
        self._load_data()

    def _load_data(self):
        """
        Loads cleaned Recipe1M+ dataset.
        """
        print(f"Loading recipes from {self.layer1_path}...")
        try:
            if not os.path.exists(self.layer1_path):
                print(f"File not found: {self.layer1_path}")
                return

            with open(self.layer1_path, 'r') as f:
                raw_recipes = json.load(f)
            
            # Create a lookup for images if layer2 is provided
            image_lookup = {}
            if self.layer2_path and os.path.exists(self.layer2_path):
                print(f"Loading images from {self.layer2_path}...")
                with open(self.layer2_path, 'r') as f:
                    raw_images = json.load(f)
                    for item in raw_images:
                         if 'images' in item and len(item['images']) > 0:
                             image_lookup[item['id']] = item['images'][0]['url']

            print(f"Processing {len(raw_recipes)} cleaned recipes...")
            
            # Increase load limit as data is much cleaner now 
            LOAD_LIMIT = 100000 
            
            self.recipes = []
            for r in raw_recipes[:LOAD_LIMIT]:
                rid = r.get('id')
                name = r.get('name', 'Untitled')
                ingredients = r.get('ingredients', [])
                
                # Build a search set from words in cleaned ingredients
                # Since ingredients are already clean, this is much more accurate
                search_set = set()
                for ing in ingredients:
                    words = ing.lower().split()
                    search_set.update(words)
                    search_set.add(ing.lower())

                self.recipes.append({
                    "id": rid,
                    "name": name,
                    "rating": "N/A",
                    "prep_time": "",
                    "cook_time": "",
                    "ingredients": [{"text": ing} for ing in ingredients],
                    "directions": r.get('instructions', []),
                    "_search_set": search_set,
                    "image_url": image_lookup.get(rid, "")
                })
                
            print(f"Loaded {len(self.recipes)} recipes into memory.")

        except Exception as e:
            print(f"Error loading datasets: {e}")
            self.recipes = []

    def search(self, detected_ingredients: list[str], limit: int = 6):
        """
        Search strategy:
        1. Exact Matches: User has ALL required ingredients (ignoring staples).
        2. Partial Matches: User has at least 20% of ingredients.
        """
        exact_matches = []
        partial_matches = []
        
        user_ingredients = {item.lower().strip() for item in detected_ingredients}
        
        for recipe in self.recipes:
            # Identify missing ingredients
            missing_ingredients = []
            matches = 0
            
            # Use strict matching: The recipe ingredient string must be one of the detected strings
            
            effective_total = 0 # meaningful ingredients count
            STAPLES = {"salt", "water", "oil", "pepper", "sugar"}
            
            for ing_dict in recipe['ingredients']:
                ing_text = ing_dict['text'].lower().strip()
                
                # Check if staple
                is_staple = False
                for staple in STAPLES:
                    if f" {staple} " in f" {ing_text} " or ing_text == staple:
                        is_staple = True
                        break
                
                if not is_staple:
                    effective_total += 1
                    # Strict matching
                    if ing_text in user_ingredients:
                        matches += 1
                    else:
                        missing_ingredients.append(ing_dict['text'])
            
            if effective_total == 0:
                continue

            coverage = matches / effective_total
            
            # Enrich recipe with missing info (create a copy/dict to avoid mutating global cache if we were caching)
            result_item = {
                "recipe": recipe,
                "missing_count": len(missing_ingredients),
                "missing_ingredients": missing_ingredients,
                "coverage": coverage
            }
            
            if len(missing_ingredients) == 0:
                exact_matches.append(result_item)
            elif coverage > 0.2: # At least 20% match for partial
                partial_matches.append(result_item)
        
        # Sort Exact: Matches desc (more ingredients used = better?) -> actually just by rating or random
        exact_matches.sort(key=lambda x: -len(x['recipe']['ingredients'])) 
        
        # Sort Partial: Coverage desc, then missing count asc
        partial_matches.sort(key=lambda x: (-x['coverage'], x['missing_count']))
        
        return {
            "exact": [item for item in exact_matches[:limit]],
            "partial": [item for item in partial_matches[:limit]]
        }

if __name__ == "__main__":
    # Test path assumptions
    # Update to use processed file
    processed_path = os.path.join(os.path.dirname(__file__), "../../recipe1M_layers/processed_layer1.json")
    layer2_path = os.path.join(os.path.dirname(__file__), "../../recipe1M_layers/layer2.json")
    matcher = RecipeMatcher(processed_path, layer2_path)
    print(f"Loaded {len(matcher.recipes)}")
    
    # Simple test search
    results = matcher.search(["chicken", "onions", "garlic"])
    print(f"Found {len(results['exact'])} exact and {len(results['partial'])} partial matches.")
    if results['exact']:
        print(f"Top exact: {results['exact'][0]['recipe']['name']}")
