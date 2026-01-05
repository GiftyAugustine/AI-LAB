from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import shutil
import os
from typing import List

from app.vlm import QwenVLAnalyzer
from app.matcher import RecipeMatcher
from app.scraper import WebRecipeScraper

# Initialize App
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize Logic
# Use relative path assuming we run from 'app' parent or adjust accordingly
# We will run uvicorn from the root folder: python -m uvicorn app.main:app
CSV_PATH = os.path.join(os.path.dirname(__file__), "../recipes.csv")
matcher = RecipeMatcher(CSV_PATH)
analyzer = QwenVLAnalyzer() # Uses default, handling CPU/MPS logic internally
web_scraper = WebRecipeScraper()

class RecipeResponse(BaseModel):
    name: str
    rating: str
    prep_time: str
    cook_time: str
    ingredients: List[dict] # Full dicts with qty/unit
    directions: List[str]
    match_score: int
    image_url: str = None
    is_web_result: bool = False

class AnalysisResponse(BaseModel):
    detected_ingredients: List[str]
    suggested_recipes: List[RecipeResponse]

@app.get("/")
async def read_index():
    return FileResponse('app/static/index.html')

@app.post("/api/process-image", response_model=AnalysisResponse)
async def process_image(file: UploadFile = File(...)):
    try:
        # Read image
        image_bytes = await file.read()
        
        # 1. Analyze with QwenVL
        detected_ingredients = analyzer.analyze(image_bytes)
        print(f"Detected: {detected_ingredients}")
        
        # 2. Match Recipes (Local CSV)
        # Attempt 1: High Strictness (Must have Main Protein if title says so, >40% coverage)
        local_matches = matcher.search(detected_ingredients, limit=3, strict_protein=True, min_coverage=0.4)
        
        # Attempt 2: Fallback (If no matches, relax strictness but maintain 40% coverage)
        if not local_matches:
            print("No strict matches found. Attempting fallback with 40% coverage rule...")
            local_matches = matcher.search(detected_ingredients, limit=3, strict_protein=False, min_coverage=0.4)
        
        # 3. Match Recipes (Web Scraping)
        # Only search if we found ingredients
        web_matches = []
        if detected_ingredients and "error" not in detected_ingredients[0]:
            print("Fetching web recipes...")
            # We also pass strict constraints to web scraper query implicitly by just searching ingredients
            web_matches = web_scraper.search_and_scrape(detected_ingredients, limit=3)
        
        # Format response
        recipes_out = []
        
        # Add Web Matches First (Priority as requested)
        for recipe in web_matches:
            recipes_out.append(RecipeResponse(
                name=recipe['name'],
                rating=str(recipe['rating']),
                prep_time=str(recipe['prep_time']),
                cook_time=str(recipe['cook_time']),
                ingredients=recipe['ingredients'],
                directions=recipe['directions'],
                match_score=100, # Artificial high score for web results
                image_url=str(recipe['image_url']) if recipe['image_url'] else "",
                is_web_result=True
            ))
            
        # Add Local Matches
        for recipe in local_matches:
            recipes_out.append(RecipeResponse(
                name=recipe['name'],
                rating=str(recipe['rating']),
                prep_time=str(recipe['prep_time']),
                cook_time=str(recipe['cook_time']),
                ingredients=recipe['ingredients'],
                directions=recipe['directions'],
                match_score=0, 
                image_url=str(recipe['image_url']) if recipe['image_url'] else "",
                is_web_result=False
            ))
            
        return AnalysisResponse(
            detected_ingredients=detected_ingredients,
            suggested_recipes=recipes_out
        )

    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
