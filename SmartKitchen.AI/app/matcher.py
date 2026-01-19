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
        Loads Recipe1M+ dataset from layer1 (text) and layer2 (images).
        """
        print(f"Loading recipes from {self.layer1_path}...")
        try:
            with open(self.layer1_path, 'r') as f:
                # layer1.json is a list of recipes
                raw_recipes = json.load(f)
            
            # Create a lookup for images if layer2 is provided
            image_lookup = {}
            if self.layer2_path and os.path.exists(self.layer2_path):
                print(f"Loading images from {self.layer2_path}...")
                with open(self.layer2_path, 'r') as f:
                    raw_images = json.load(f)
                    # layer2 struct: [{"id": "...", "images": [{"url": "...", "id": "..."}]}, ...]
                    for item in raw_images:
                         if 'images' in item and len(item['images']) > 0:
                             image_lookup[item['id']] = item['images'][0]['url']

            print(f"Processing {len(raw_recipes)} recipes...")
            
            # Limit to 50k for performance if needed, or keep all if memory allows. 
            # 1.4GB json might be heavy. Let's load the first 20,000 for now to be safe on local machine.
            # User can increase this limit.
            LOAD_LIMIT = 20000 
            
            count = 0
            for r in raw_recipes:
                if count >= LOAD_LIMIT:
                    break
                    
                rid = r.get('id')
                title = r.get('title', 'Untitled')
                
                # Ingredients in layer1 are often [{"text": "..."}]
                ingredients_raw = r.get('ingredients', [])
                valid_ingredients = []
                search_set = set()
                
                for ing in ingredients_raw:
                    text = ing.get('text', '')
                    valid_ingredients.append({"text": text}) # simpler struct
                    # Add to search set
                    search_set.add(text.lower())
                    for word in text.split():
                        if len(word) > 2:
                            search_set.add(word.lower())

                instructions = []
                for inst in r.get('instructions', []):
                    instructions.append(inst.get('text', ''))

                self.recipes.append({
                    "id": rid,
                    "name": title,
                    "rating": "N/A", # Layer1 implementation doesn't strictly have ratings usually
                    "prep_time": "",
                    "cook_time": "",
                    "ingredients": valid_ingredients,
                    "directions": instructions,
                    "_search_set": search_set,
                    "image_url": image_lookup.get(rid, "")
                })
                count += 1
                
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
        
        user_tokens = set()
        for item in detected_ingredients:
            words = [w.lower() for w in item.split() if len(w) > 2]
            user_tokens.update(words)
            
        for recipe in self.recipes:
            recipe_search_set = recipe['_search_set']
            
            # Identify missing ingredients
            missing_ingredients = []
            matches = 0
            
            # We need to check each ingredient line to see if it's "covered"
            # This is an approximation because _search_set is a flat set of all words.
            # A more robust way: Check if ANY word from the user tokens appears in the ingredient text.
            
            effective_total = 0 # meaningful ingredients count
            STAPLES = {"salt", "water", "oil", "pepper", "sugar", "butter"}
            
            for ing_dict in recipe['ingredients']:
                ing_text = ing_dict['text'].lower()
                
                # Check if staple
                is_staple = False
                for staple in STAPLES:
                    if f" {staple} " in f" {ing_text} " or ing_text == staple:
                        is_staple = True
                        break
                
                if not is_staple:
                    effective_total += 1
                    # Check coverage
                    # If any user token is in this ingredient text, we count it as matched
                    # (Simple heuristic)
                    if any(token in ing_text for token in user_tokens):
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
    matcher = RecipeMatcher("../../recipe1M_layers/layer1.json", "../../recipe1M_layers/layer2.json")
    print(f"Loaded {len(matcher.recipes)}")
