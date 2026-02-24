# 📦 Project Dependencies Breakdown

This document explains each requirement in `requirements.txt`, why it is used, and which part of the SmartKitchen.AI ecosystem it supports.

---

## 🌐 Web & API Layer
These libraries form the foundation of our communication and user interface server.

### **FastAPI**
- **What**: A modern, high-performance web framework for building APIs with Python.
- **Why**: It is extremely fast and supports asynchronous programming (`async/await`), which allows our server to handle multiple recipe searches simultaneously without blocking.

### **Uvicorn**
- **What**: An ASGI (Asynchronous Server Gateway Interface) server implementation.
- **Why**: It acts as the "engine" that runs the FastAPI application. While FastAPI defines the logic, Uvicorn delivers the data to your browser.

### **Python-Multipart**
- **What**: A parser for multipart form data.
- **Why**: Required by FastAPI to handle **image uploads**. Without this, the server wouldn't be able to read the photos you send from your camera or gallery.

---

## 🤖 Vision Intelligence (AI/ML)
These libraries power the "Eyes" of the application—identifying food from your photos.

### **Torch & Torchvision**
- **What**: PyTorch is the primary deep learning framework. Torchvision provides tools and pre-trained models for computer vision.
- **Why**: They are the low-level engines that execute the mathematical operations required by our Vision Language Model (VLM) on your CPU or GPU.

### **Transformers**
- **What**: A library by Hugging Face providing state-of-the-art machine learning models.
- **Why**: It is used to download, load, and run the **Qwen2-VL** model. It manages the complex architecture of the VLM.

### **Qwen-VL-Utils**
- **What**: Specialized utilities for the Qwen-VL model series.
- **Why**: It handles the specific formatting of vision-language inputs (images + text prompts) that the Qwen model requires to understand its "vision" task.

### **Accelerate**
- **What**: A library to run PyTorch models on any configuration (CPU, GPU, MPS) with ease.
- **Why**: It helps us optimize the model for local execution, ensuring it can tap into your Mac's **MPS (Metal)** chip for faster performance.

### **Pillow (PIL)**
- **What**: The Python Imaging Library.
- **Why**: Used for all image manipulations—opening, resizing, and optimizing your photos before they are sent to the AI for analysis.

---

## 📊 Data Processing & Evaluation
Used for managing the nearly 1 million recipes and analyzing performance.

### **Pandas**
- **What**: A powerful data analysis and manipulation library.
- **Why**: Used in evaluation scripts (like `evaluation/evaluate.py`) to efficiently handle large results in a table-like format and export reports to CSV.

### **BeautifulSoup4**
- **What**: A library for pulling data out of HTML and XML files.
- **Why**: Used for parsing web data. It is a critical dependency for our (currently disabled) recipe scraping engine to extract ingredients from messy website layouts.

---

## 🕸️ Web Scraping Engine
These libraries allow the app to "look up" recipes online when the local database doesn't have a perfect match.

### **DuckDuckGo-Search**
- **What**: A library to perform searches on DuckDuckGo without an API key.
- **Why**: It allows the app to find new recipe pages on the fly based on the ingredients detected by the AI.

### **Recipe-Scrapers**
- **What**: A specialized library that can extract ingredients and instructions from over 100 popular recipe websites.
- **Why**: It does the "heavy lifting" of converting a raw URL (like an AllRecipes link) into structured data for our UI.
