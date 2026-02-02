# SmartKitchen.AI Technical Overview

SmartKitchen.AI is an AI-powered culinary assistant that identifies ingredients from images and suggests recipes using an optimized matching algorithm against 876,997 preprocessed recipes.

---

## 🚀 Key Technologies Explained

To understand how SmartKitchen.AI works, here is a breakdown of the core technologies used in this project:

### 🟢 **FastAPI**
FastAPI is the modern, high-performance web framework used for the backend. It is called "Fast" because it is one of the fastest Python frameworks available, rivaling NodeJS and Go. It uses **Asynchronous (async)** programming, allowing the server to handle multiple requests (like image uploads and recipe searches) simultaneously without one task blocking another.

### 🟢 **VLM (Vision Language Model)**
A Vision Language Model is a type of AI that can "see" images and "speak" text. Unlike basic image classifiers that just pick a category (e.g., "dog" or "cat"), a VLM understands the context. In this app, we use **Qwen2-VL-2B**, which can read recipe ingredients, identify textures, and even understand quantities from a photo.

### 🟢 **Glassmorphism**
This is the UI design style used for the frontend. It creates a "frosted glass" effect where interface elements have semi-transparent backgrounds with a subtle blur. This gives the application a premium, modern, and deep aesthetic, making it feel more like a native high-end app rather than a simple webpage.

### 🟢 **BFloat16 (Brain Floating Point 16)**
This is a specialized mathematical format used by AI models to save memory. Standard computers use Float32 (32 bits), but AI models are so large that they would eat up all your RAM. BFloat16 cuts the size in half while keeping the most important information intact, allowing the 2-billion parameter Qwen model to run smoothly on home computers.

### 🟢 **MPS (Metal Performance Shaders)**
On macOS, we use MPS to tap into the power of Apple's **M1/M2/M3 chips**. It allows the AI model to run on your Mac's GPU (Graphics Processing Unit) instead of just the CPU. This results in ingredient detection that is often 5-10 times faster than CPU-only processing.

### 🟢 **Uvicorn**
Uvicorn is the "engine" that runs the FastAPI application. It is an **ASGI (Asynchronous Server Gateway Interface)** server. While FastAPI defines the logic, Uvicorn acts as the delivery man, receiving requests from the internet and passing them into the code.

---

## ⚙️ Core Components

### 📂 `app/main.py`
The "Brain" of the communication layer.
- **Dynamic Routing**: Manages the API endpoints.
- **Static Hosting**: Efficiently serves the glassmorphic frontend to your browser.
- **Workflow Management**: Coordinates between the image analyzer and the recipe matcher.

### 📂 `app/vlm.py`
The "Eyes" of the application.
- **Model Loading**: Dynamically switches to **CPU** or **MPS (GPU)** based on your hardware.
- **Image Processing**: Resizes and optimizes your photos before sending them to the AI to ensure fast response times.
- **Ingredient Extraction**: Converts visual data into a comma-separated list of text ingredients.

### 📂 `app/matcher.py`
The "Knowledge Base."
- **Full Library**: Now loads over **876,997 cleaned recipes** into memory for instant searching.
- **Exact Staple Logic**: We use a strict filter for staple foods (salt, sugar, water, oil). It only skips these if they are exact matches, ensuring "olive oil" or "sea salt" are correctly treated as unique ingredients.
- **Refined Matching**: Calculates **Coverage Score** (how many items you have vs. how many you need) and provides "Perfect Matches" vs "Partial Matches."

---

## 🧹 Data Preprocessing (`clean_dataset.py`)
Because the raw dataset (1.4GB) is messy, we run a cleaning script that:
1. **De-noises**: Removes units like "1 tsp" or "200g" so that only the word "chicken" remains.
2. **Filters**: Skips recipes that are just spice mixes or drinks, focusing on actual meals.
3. **Augments**: If a recipe says "fry in oil" in the instructions but forgets "oil" in the list, the script finds it and adds it back.

## 🎨 UI Refinements
The UI has been streamlined to remove unnecessary metadata:
- **Clean Interface**: Time taken and Star Ratings have been removed to focus entirely on the ingredients and directions.
- **Dynamic Tags**: Users can add or remove ingredients identified by the AI to refine their search results manually.
