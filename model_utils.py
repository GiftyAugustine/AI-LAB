import requests
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def analyze_image_with_model(image_b64):
    """
    Sends an image (base64 string) to the Qwen 2.5 VL model via OpenRouter
    to extract a list of ingredients.
    """
    print("Sending image to Qwen 2.5 VLM for ingredient analysis...")

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

    try:
        # Send request to OpenRouter
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        print("API Response:", r.status_code)
        
        if r.status_code != 200:
             print(f"API Error: {r.text}")
             return f"API Error: {r.status_code}"

        data = r.json()

        if "choices" in data:
            ingredients = data["choices"][0]["message"]["content"]
            print(f"Qwen extracted ingredients: {ingredients}")
            return ingredients
        elif "error" in data:
            return f"API Error: {data['error'].get('message', 'Unknown error')}"
        else:
            return "Unexpected response format. Please try again."

    except Exception as e:
        print("Error in analyze_image_with_model:", e)
        traceback.print_exc()
        return f"Server error: {str(e)}"
