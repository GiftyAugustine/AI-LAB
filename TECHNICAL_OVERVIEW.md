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

## 🤖 Model Selection: Why Qwen2-VL-2B?

While newer series like **Qwen2.5-VL** and **Qwen3-VL** exist, SmartKitchen.AI uses **Qwen2-VL-2B** for the following specific reasons:

1.  **Qwen2.5-VL (No 2B Version)**: The 2.5 series starts at **3B parameters**. We tested the 3B model and found it frequently caused **MPS (Metal) Out-of-Memory** errors on baseline MacBooks (8GB-16GB RAM). Without a 2B option in this series, it remains too heavy for local consumer use.
2.  **Qwen3-VL (Recent Release)**: The **Qwen3-VL-2B** was released in late October 2025. While it shows great promise for edge device efficiency (Raspberry Pi, laptops), **Qwen2-VL-2B** was the established, stable choice during our core development. We may consider Qwen3 for a future performance-focused update.
3.  **Stability & Speed**: The 2B variant provides the best balance of inference speed and accuracy on local hardware. Larger or significantly newer models often require specialized optimizations (like quantization) or updated drivers that may not be standard on all user setups.

---

## 🔒 Privacy & Local Ownership (No API Tokens)

You may wonder why SmartKitchen.AI doesn't just use an API token for a cloud service like OpenAI (GPT-4) or Google Gemini. This was a deliberate architectural choice based on three core values:

1.  **Absolute Privacy**: Your kitchen is a private space. By running the VLM locally, your photos never leave your machine. No cloud provider gets to see or store what's inside your fridge.
2.  **Zero Ongoing Costs**: Cloud Vision APIs typically cost between **$0.01 and $0.05 per image**. For a user experimenting with recipes daily, this adds up. A local model is free to use forever once downloaded.
3.  **Offline Capability**: SmartKitchen.AI is designed to be functional even without an internet connection. By hosting the "brain" of the app locally, the ingredient detection remains fast and reliable regardless of your Wi-Fi signal.

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
