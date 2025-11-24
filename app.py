import warnings
warnings.filterwarnings("ignore", message="NotOpenSSLWarning")

from flask import Flask, request, jsonify
import requests, base64, os, sqlite3
from flask_cors import CORS
from dotenv import load_dotenv
import traceback

# Load environment variables (API key)
load_dotenv()

app = Flask(__name__)
CORS(app)

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

        print("✅ Image received. Sending to Qwen 2.5 VLM for ingredient analysis...")

        payload = {
            "model": "qwen/qwen-2.5-vl-7b-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert visual recognition assistant. "
                        "Analyze the image and extract a clean list of ingredients or food items visible. "
                        "Output them as a simple list with quantities or counts if possible. "
                        "Do NOT describe the scene, colors, or background. "
                        "Format strictly like this: Bananas – 4, Apples – 3, Tomatoes – 2"
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "List only the ingredients you detect in this image:"},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"}
                    ]
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        # Send request to OpenRouter
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        print("🌐 API Response:", r.status_code)
        print("🔹 Raw Response Preview:", r.text[:400])

        try:
            data = r.json()
        except Exception as e:
            print("❌ Error decoding JSON:", e)
            traceback.print_exc()
            return jsonify({"result": "⚠️ Could not parse API response."}), 500

        if "choices" in data:
            ingredients = data["choices"][0]["message"]["content"]
            print(f"🧠 Qwen extracted ingredients: {ingredients}")
        elif "error" in data:
            ingredients = f"⚠️ API Error: {data['error'].get('message', 'Unknown error')}"
        else:
            ingredients = "⚠️ Unexpected response format. Please try again."

        # --- 🔹 NEW: Query recipes database using extracted ingredients ---
        recipes = search_recipes(ingredients)

        response = {
            "ingredients": ingredients,
            "recipes": recipes
        }

        return jsonify(response)

    except Exception as e:
        print("❌ Exception in /analyze:", e)
        traceback.print_exc()
        return jsonify({"result": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    print("🚀 Starting SmartKitchen.AI backend server...")
    app.run(host="0.0.0.0", port=5001)
