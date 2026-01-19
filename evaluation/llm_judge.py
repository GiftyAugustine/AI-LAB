import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def evaluate_with_llm(predicted_ingredients, ground_truth_ingredients):
    """
    Uses an LLM to compare predicted ingredients with ground truth.
    Returns a score (0-10) and an explanation.
    """
    print("⚖️ Asking LLM to judge the prediction...")

    prompt = f"""
    Compare the following two lists of ingredients:
    
    Ground Truth: {ground_truth_ingredients}
    Predicted: {predicted_ingredients}
    
    Task:
    1. Identify correctly detected items (accounting for synonyms like 'cilantro'/'coriander').
    2. Identify missed items.
    3. Identify hallucinated items (items in prediction but not in ground truth).
    4. Assign a score from 0 to 10 based on accuracy (10 = perfect match).
    
    Output JSON format:
    {{
        "score": <number>,
        "explanation": "<short explanation>",
        "missed": [<list of missed items>],
        "hallucinated": [<list of extra items>]
    }}
    """

    payload = {
        "model": "qwen/qwen-2.5-72b-instruct", # Using a strong text model for evaluation
        "messages": [
            {"role": "system", "content": "You are a fair and strict judge of AI model performance."},
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if r.status_code != 200:
            print(f"❌ LLM Judge API Error: {r.text}")
            return {"score": 0, "explanation": "API Error"}

        content = r.json()["choices"][0]["message"]["content"]
        
        # Attempt to parse JSON from the response (it might be wrapped in markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
             content = content.split("```")[1].split("```")[0].strip()
             
        return json.loads(content)

    except Exception as e:
        print(f"❌ Error in LLM Judge: {e}")
        return {"score": 0, "explanation": f"Error: {str(e)}"}
