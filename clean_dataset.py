import json
import re
import os
import sys

# Common units and measures to strip
UNITS = {
    'ounce', 'ounces', 'oz', 'cup', 'cups', 'c', 'tablespoon', 'tablespoons', 'tbsp', 'tbs',
    'teaspoon', 'teaspoons', 'tsp', 'pound', 'pounds', 'lb', 'lbs', 'kg', 'g', 'gram', 'grams',
    'ml', 'l', 'liter', 'liters', 'package', 'pkg', 'can', 'bottle', 'stick', 'batch', 'container',
    'clove', 'cloves', 'pinch', 'dash', 'sprig', 'sprigs', 'head', 'heads', 'piece', 'pieces',
    'slice', 'slices', 'bag', 'bags', 'jar', 'jars', 'tub', 'tubs', 'box', 'boxes', 'can', 'cans',
    'cloves', 'small', 'medium', 'large', 'big', 'bunch', 'bunches', 'weight'
}

# Common culinary descriptors to strip
DESCRIPTORS = {
    'chopped', 'grated', 'minced', 'sliced', 'diced', 'peeled', 'fresh', 'raw', 'frozen', 'dried',
    'shredded', 'crushed', 'melted', 'softened', 'cooked', 'beaten',
    'halved', 'quartered', 'finely', 'coarsely', 'thinly', 'thickly', 'optional', 'plus', 'to taste',
    'dry', 'wet', 'cold', 'warm', 'hot', 'all-purpose', 'kosher', 'extra-virgin', 'black', 'white',
    'ground', 'whole', 'unsalted', 'salted', 'low-fat', 'fat-free', 'reduced-sodium', 'canned',
    'freshly', 'roughly', 'prepared', 'extra', 'virgin', 'divided', 'for', 'to', 'or'
}

# Common ingredients to check for in instructions if missing from list
COMMON_INGREDIENTS = [
    'salt', 'pepper', 'water', 'oil', 'butter', 'sugar', 'flour', 'milk', 'egg', 'eggs', 
    'garlic', 'onion', 'lemon', 'lime', 'cinnamon', 'vanilla', 'yeast', 'baking powder', 
    'baking soda', 'honey', 'olive oil', 'vegetable oil', 'vinegar', 'parsley', 'cilantro',
    'basil', 'oregano', 'thyme', 'rosemary', 'scallops', 'scallions', 'ginger', 'soy sauce'
]

# Recipes with these keywords in title are almost always components/mixes
ALWAYS_SKIP_KEYWORDS = {
    'powder', 'extract', 'essence', 'seasoning', 'spice rub', 'spice mix', 
    'infusion', 'liqueur', 'concentrate', 'varnish', 'puree'
}

# Recipes with these in title are likely sub-components if they have few ingredients
CONDITIONAL_SKIP_KEYWORDS = {
    'sauce', 'glaze', 'syrup', 'dressing', 'oil', 'stock', 'broth', 'paste', 
    'dip', 'marinade', 'rub', 'vinegar', 'butter', 'cream', 'jam', 'jelly', 
    'pickle', 'pesto', 'hummus', 'compote', 'coulis'
}

def normalize_ingredient(text):
    text = text.lower()
    # Remove everything in parentheses
    text = re.sub(r'\(.*?\)', '', text)
    # Remove numbers and fractions (including common Unicode fractions)
    text = re.sub(r'[\d\u00BC-\u00BE\u2150-\u215E]+(/[ \d\u00BC-\u00BE\u2150-\u215E]+)?', ' ', text)
    # Remove special chars (keep spaces and letters)
    text = re.sub(r'[^a-z ]', ' ', text)
    
    # Strip units and descriptors
    words = text.split()
    cleaned_words = []
    for word in words:
        if word not in UNITS and word not in DESCRIPTORS and len(word) > 1:
            cleaned_words.append(word)
    
    # Clean up common plurals/variations simple way
    res = ' '.join(cleaned_words)
    if res.endswith('s') and len(res) > 4 and res[:-1] not in ['bass', 'loss', 'less']:
        # very simple stemming for matching
        pass 
    return res

def process_recipe(r):
    title = r.get('title', 'Untitled')
    ingredients_raw = r.get('ingredients', [])
    instructions_raw = r.get('instructions', [])
    
    # Filter: Non-dish check
    title_lower = title.lower()
    
    # Always skip if certain keywords are in title
    if any(kw in title_lower for kw in ALWAYS_SKIP_KEYWORDS):
        return None
        
    # Skip if conditional keywords are present and ingredient count is low
    # Components like "Sauce" with < 6 ingredients are likely sub-recipes
    if len(ingredients_raw) < 6:
        if any(kw in title_lower for kw in CONDITIONAL_SKIP_KEYWORDS):
            return None
            
    # Extra check: "Homemade X" where X is a conditional keyword
    if "homemade" in title_lower and any(kw in title_lower for kw in CONDITIONAL_SKIP_KEYWORDS):
        if len(ingredients_raw) < 8: # Even more aggressive if labeled as homemade
            return None
            
    # New Filter: Max 6 words in title
    if len(title.split()) > 6:
        return None
            
    # Normalize ingredients
    processed_ingredients = []
    seen_ingredients = set()
    for ing in ingredients_raw:
        norm = normalize_ingredient(ing.get('text', ''))
        if norm and norm not in seen_ingredients:
            processed_ingredients.append(norm)
            seen_ingredients.add(norm)
            
    # Augment from instructions
    instruction_text = ' '.join([inst.get('text', '').lower() for inst in instructions_raw])
    for common in COMMON_INGREDIENTS:
        # Avoid double counting "oil" if "olive oil" is present
        is_already_present = False
        for seen in seen_ingredients:
            if common in seen:
                is_already_present = True
                break
        
        if not is_already_present and re.search(rf'\b{common}\b', instruction_text):
            processed_ingredients.append(common)
            seen_ingredients.add(common)
            
    # Final check: if we ended up with almost no ingredients, skip
    if len(processed_ingredients) < 2:
        return None
        
    return {
        "id": r.get('id'),
        "name": title,
        "ingredients": processed_ingredients,
        "instructions": [inst.get('text', '') for inst in instructions_raw]
    }

def main():
    input_path = '/Users/divyasabu/Desktop/AI-LAB/recipe1M_layers/layer1.json'
    output_path = '/Users/divyasabu/Desktop/AI-LAB/recipe1M_layers/processed_layer1.json'
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    print(f"Processing {input_path}...")
    count = 0
    saved_count = 0
    
    # Remove limit for full dataset processing
    LIMIT = float('inf') 
    
    with open(input_path, 'r') as fin, open(output_path, 'w') as fout:
        fout.write('[\n')
        first = True
        for line in fin:
            line = line.strip()
            if not line or line == '[':
                continue
            if line == ']':
                break
            
            # Remove trailing comma
            if line.endswith(','):
                line = line[:-1]
                
            try:
                recipe = json.loads(line)
                processed = process_recipe(recipe)
                count += 1
                
                if processed:
                    if not first:
                        fout.write(',\n')
                    fout.write(json.dumps(processed))
                    first = False
                    saved_count += 1
                
                if count % 1000 == 0:
                    print(f"Processed {count} recipes, saved {saved_count}...", end='\r')
                
                if count >= LIMIT:
                    break
                    
            except Exception as e:
                continue
        
        fout.write('\n]')
    
    print(f"\nFinished! Processed {count} recipes. Saved {saved_count} clean recipes to {output_path}.")

if __name__ == "__main__":
    main()
