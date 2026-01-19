from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import shutil
import os
from typing import List

from app.vlm import QwenVLAnalyzer
from app.matcher import RecipeMatcher
# from app.scraper import WebRecipeScraper (Removed)

# Initialize App
# Initialize App
app = FastAPI()

# Make paths robust regardless of execution directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize Logic
# Use relative path assuming we run from 'app' parent or adjust accordingly
# We will run uvicorn from the root folder: python -m uvicorn app.main:app
DATASET_DIR = r"C:\Users\kezia\recipe1M_layers"
LAYER1_PATH = os.path.join(DATASET_DIR, "layer1.json")
LAYER2_PATH = os.path.join(DATASET_DIR, "layer2.json")
matcher = RecipeMatcher(LAYER1_PATH, LAYER2_PATH)
analyzer = QwenVLAnalyzer() # Uses default, handling CPU/MPS logic internally

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
    missing_count: int = 0
    missing_ingredients: List[str] = []

class AnalysisResponse(BaseModel):
    detected_ingredients: List[str]
    exact_matches: List[RecipeResponse]
    partial_matches: List[RecipeResponse]

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.post("/api/process-image", response_model=AnalysisResponse)
async def process_image(file: UploadFile = File(...)):
    try:
        # Read image
        image_bytes = await file.read()
        
        # 1. Analyze with QwenVL
        detected_ingredients = analyzer.analyze(image_bytes)
        print(f"Detected (Raw): {detected_ingredients}")
        
        # Deduplicate while preserving order
        seen = set()
        unique_ingredients = []
        for ing in detected_ingredients:
            lower = ing.lower().strip()
            if lower and lower not in seen:
                seen.add(lower)
                unique_ingredients.append(ing) # Keep original casing of first occurrence
        detected_ingredients = unique_ingredients
        print(f"Detected (Unique): {detected_ingredients}")
        
        # 2. Match Recipes (Local JSON)
        matches = matcher.search(detected_ingredients, limit=5)
        
        # Helper to format list
        def format_list(match_list):
            out = []
            for item in match_list:
                recipe = item['recipe']
                
                # Clean ingredients format for frontend
                clean_ingredients = []
                for ing in recipe['ingredients']:
                    clean_ingredients.append({"name": ing['text'], "qty": ""})

                out.append(RecipeResponse(
                    name=recipe['name'],
                    rating=str(recipe['rating']),
                    prep_time=str(recipe['prep_time']),
                    cook_time=str(recipe['cook_time']),
                    ingredients=clean_ingredients,
                    directions=recipe['directions'],
                    match_score=int(item['coverage'] * 100), 
                    image_url=str(recipe['image_url']) if recipe['image_url'] else "",
                    is_web_result=False,
                    missing_count=item['missing_count'],
                    missing_ingredients=item['missing_ingredients']
                ))
            return out

        return AnalysisResponse(
            detected_ingredients=detected_ingredients,
            exact_matches=format_list(matches['exact']),
            partial_matches=format_list(matches['partial'])
        )

    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class SearchRequest(BaseModel):
    ingredients: List[str]

@app.post("/api/search-recipes", response_model=AnalysisResponse)
async def search_recipes(request: SearchRequest):
    try:
        # Match Recipes (Local JSON)
        matches = matcher.search(request.ingredients, limit=5)
        
        # Helper to format list
        def format_list(match_list):
            out = []
            for item in match_list:
                recipe = item['recipe']
                
                # Clean ingredients format for frontend
                clean_ingredients = []
                for ing in recipe['ingredients']:
                    clean_ingredients.append({"name": ing['text'], "qty": ""})

                out.append(RecipeResponse(
                    name=recipe['name'],
                    rating=str(recipe['rating']),
                    prep_time=str(recipe['prep_time']),
                    cook_time=str(recipe['cook_time']),
                    ingredients=clean_ingredients,
                    directions=recipe['directions'],
                    match_score=int(item['coverage'] * 100), 
                    image_url=str(recipe['image_url']) if recipe['image_url'] else "",
                    is_web_result=False,
                    missing_count=item['missing_count'],
                    missing_ingredients=item['missing_ingredients']
                ))
            return out

        return AnalysisResponse(
            detected_ingredients=request.ingredients,
            exact_matches=format_list(matches['exact']),
            partial_matches=format_list(matches['partial'])
        )

    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
