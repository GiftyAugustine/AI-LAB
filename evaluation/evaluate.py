import json
import os
import sys
import base64
import pandas as pd

# Add parent directory to path to import model_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_utils import analyze_image_with_model
from llm_judge import evaluate_with_llm

GROUND_TRUTH_FILE = "evaluation/ground_truth.json"
IMAGE_DIR = "evaluation/images"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def main():
    print("Starting Evaluation Pipeline...")
    
    if not os.path.exists(GROUND_TRUTH_FILE):
        print(f"Ground truth file not found: {GROUND_TRUTH_FILE}")
        return

    with open(GROUND_TRUTH_FILE, "r") as f:
        ground_truth = json.load(f)

    results = []

    for image_name, expected_ingredients in ground_truth.items():
        image_path = os.path.join(IMAGE_DIR, image_name)
        
        print(f"\nProcessing {image_name}...")
        
        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}. Skipping.")
            results.append({
                "image": image_name,
                "status": "Missing Image",
                "score": 0,
                "explanation": "Image not found",
                "predicted": "",
                "ground_truth": "",
                "missed": "",
                "hallucinated": ""
            })
            continue

        # 1. Get Model Prediction
        image_b64 = encode_image(image_path)
        predicted_text = analyze_image_with_model(image_b64)
        
        # 2. Evaluate with LLM
        evaluation = evaluate_with_llm(predicted_text, expected_ingredients)
        
        print(f"   Score: {evaluation.get('score')}/10")
        print(f"   Explanation: {evaluation.get('explanation')}")

        results.append({
            "image": image_name,
            "status": "Success",
            "predicted": predicted_text,
            "ground_truth": str(expected_ingredients),
            "score": evaluation.get("score"),
            "explanation": evaluation.get("explanation"),
            "missed": str(evaluation.get("missed")),
            "hallucinated": str(evaluation.get("hallucinated"))
        })

    # 3. Generate Report
    df = pd.DataFrame(results)
    print("\nEvaluation Summary:")
    print(df[["image", "score", "explanation"]])
    
    avg_score = df[df["status"] == "Success"]["score"].mean()
    print(f"\nAverage Score: {avg_score:.2f} / 10")
    
    df.to_csv("evaluation/report.csv", index=False)
    print("\nReport saved to evaluation/report.csv")

if __name__ == "__main__":
    main()
