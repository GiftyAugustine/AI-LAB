import pandas as pd
import ast
from collections import Counter

class RecipeMatcher:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self.recipes = []
        self._preprocess()

    def _preprocess(self):
        """
        Preprocesses the dataframe to parse ingredients and create search sets.
        """
        for index, row in self.df.iterrows():
            try:
                # Parse ingredients from string representation of list of dicts
                # Handling python-style string with single quotes
                ing_str = row['Ingredients']
                ingredients = ast.literal_eval(ing_str)
                
                # Parse directions
                dir_str = row['Directions']
                directions = ast.literal_eval(dir_str)
                
                # Extract search keywords (names of ingredients)
                # Normalize to lowercase for better matching
                ingredient_names = set()
                for ing in ingredients:
                    if 'name' in ing and ing['name']:
                        # Simple tokenization: "skinless, boneless chicken" -> "chicken"
                        # But for now, let's keep full phrases and individual words
                        full_name = ing['name'].lower()
                        ingredient_names.add(full_name)
                        # Add individual words too
                        for word in full_name.split():
                            if len(word) > 2: # filter out 'of', 'in' etc roughly
                                ingredient_names.add(word)

                self.recipes.append({
                    "id": index,
                    "name": row['Name'],
                    "rating": row.get('Rating', 'N/A'), # Handle missing columns gracefully
                    "prep_time": row.get('Prep Time', ''),
                    "cook_time": row.get('Cook Time', ''),
                    "ingredients": ingredients,
                    "directions": directions,
                    "_search_set": ingredient_names,
                    "image_url": row.get('url', None) # Using URL as image placeholder if needed
                })
            except Exception as e:
                print(f"Error parsing row {index}: {e}")
                continue

    def search(self, detected_ingredients: list[str], limit: int = 6, strict_protein: bool = True, min_coverage: float = 0.4):
        """
        Search for recipes.
        Ranking Strategy:
        Sort by 'Coverage Percentage'.
        """
        scored_recipes = []
        
        # User's detected items cleaned
        user_tokens = set()
        for item in detected_ingredients:
            # simple tokenization
            words = [w.lower() for w in item.split() if len(w) > 2]
            user_tokens.update(words)
        
        # Keywords that MUST be present in detected items if they appear in Recipe Title
        # e.g. If Title has "Chicken", User MUST have "chicken" in their list.
        PROTEIN_KEYWORDS = ["chicken", "steak", "beef", "pork", "shrimp", "fish", "salmon", "tuna", "lamb", "tofu"]
        
        # Common staples to ignore in the denominator (total count) to make coverage score more "fair"
        # If a recipe is 50% water and salt, we shouldn't penalize the user for not photographing water and salt.
        STAPLES = {"salt", "water", "olive oil", "vegetable oil", "oil", "pepper", "black pepper", "sugar", "butter"}
        
        for recipe in self.recipes:
            recipe_ingredients = recipe['ingredients']
            
            # Calculate Effective Total (ignoring staples)
            effective_ingredients = []
            for ing in recipe_ingredients:
                name = ing.get('name', '').lower()
                # If the name is roughly just a staple, ignore it
                # Check exact match or simple variation
                is_staple = False
                if name in STAPLES:
                    is_staple = True
                else:
                    # check if name is e.g. "1 cup water" (parsed name usually just "water" but let's be safe)
                    # Our parser extracted 'name' from the weird string.
                    # Let's simple check if any staple word is the main part
                    for staple in STAPLES:
                        if name == staple or name == f"ground {staple}":
                            is_staple = True
                            break
                
                if not is_staple:
                    effective_ingredients.append(ing)
            
            total_effective = len(effective_ingredients)
            if total_effective == 0:
                total_effective = 1 # avoid div zero
            
            recipe_title_lower = recipe['name'].lower()
            
            if len(recipe_ingredients) == 0:
                continue
                
            # STRICT CHECK 1: Title mismatch (Only if strict_protein is True)
            if strict_protein:
                forbidden = False
                for prot in PROTEIN_KEYWORDS:
                    if prot in recipe_title_lower:
                        # check if user has this protein
                        if not any(prot in t for t in user_tokens):
                            forbidden = True
                            break
                if forbidden:
                    continue

            matches = 0
            
            # Check overlap against ALL ingredients (we still match against staples if user has them? 
            # No, user rarely detects staples. But if we detected 'butter', it should count?
            # Let's count matches against the WHOLE list, but divide by EFFECTIVE list.
            # This favors the user.
            for ing_dict in recipe_ingredients:
                ing_name = ing_dict.get('name', '').lower()
                ing_words = [w for w in ing_name.split() if len(w) > 2]
                
                # Check for overlap
                if any(w in user_tokens for w in ing_words):
                    matches += 1
            
            if matches > 0:
                coverage_score = matches / total_effective
                
                # STRICT CHECK 2: Minimum Coverage
                if coverage_score < min_coverage:
                    continue
                    
                scored_recipes.append((coverage_score, matches, recipe))
        
        # Sort by coverage descending
        scored_recipes.sort(key=lambda x: (x[0], x[1]), reverse=True)
        
        return [item[2] for item in scored_recipes[:limit]]

if __name__ == "__main__":
    # Test
    matcher = RecipeMatcher("../recipes.csv")
    results = matcher.search(["chicken", "onion"])
    print(f"Found {len(results)} matches.")
    if results:
        print(results[0]['name'])
