import warnings
warnings.filterwarnings("ignore", message="NotOpenSSLWarning")

from flask import Flask, request, jsonify
import requests, base64, os, sqlite3
from flask_cors import CORS
from dotenv import load_dotenv
import traceback

# Load environment variables (API key)
load_dotenv()

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/upload.html')
def upload_page():
    return app.send_static_file('upload.html')

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DB_FILE = "recipes.db"  # local database

# --------------------------------------------
# Utility: Search recipes in local SQLite DB
# --------------------------------------------
def search_recipes(ingredients_text, limit=5):
    """Search recipes whose ingredients match any of the detected ingredient keywords."""
    try:
        if not os.path.exists(DB_FILE):
            print("⚠️ Database not found. Skipping recipe search.")
            return []

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        keywords = [word.strip().lower() for word in ingredients_text.split(",") if word.strip()]
        if not keywords:
            return []

        query = " OR ".join([f"ingredients MATCH ?" for _ in keywords])
        cursor.execute(f"SELECT name, ingredients FROM recipes WHERE {query} LIMIT {limit}", keywords)
        results = cursor.fetchall()
        conn.close()

        print(f"🔍 Found {len(results)} recipe matches.")
        return [{"name": r[0], "ingredients": r[1]} for r in results]

    except Exception as e:
        print("❌ Error during recipe search:", e)
        traceback.print_exc()
        return []


# --------------------------------------------
# Main AI Image Analysis Endpoint
# --------------------------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        if "image" not in request.files:
            return jsonify({"result": " No image received. Please upload a file."}), 400

        file = request.files["image"]
        image_b64 = base64.b64encode(file.read()).decode("utf-8")

        print("Image received. Sending to Qwen 2.5 VLM for ingredient analysis...")

        # Use the extracted function from model_utils
        from model_utils import analyze_image_with_model
        ingredients = analyze_image_with_model(image_b64)

        # --- NEW: Query recipes database using extracted ingredients ---
        recipes = search_recipes(ingredients)

        response = {
            "ingredients": ingredients,
            "recipes": recipes
        }

        return jsonify(response)

    except Exception as e:
        print("Exception in /analyze:", e)
        traceback.print_exc()
        return jsonify({"result": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    print("Starting SmartKitchen.AI backend server...")
    app.run(host="0.0.0.0", port=5001)
