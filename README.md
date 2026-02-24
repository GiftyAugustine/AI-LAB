# 🍳 SmartKitchen.AI

### Your AI-Powered Culinary Assistant

SmartKitchen.AI is an intelligent culinary assistant that identifies food ingredients from images and suggests recipes using an optimized matching algorithm against over **876,000 preprocessed recipes**.

---

## ✨ Key Features

- **📸 Vision-to-Recipe**: Upload a photo of your ingredients, and our local **Qwen2-VL** model will identify them instantly.
- **🔍 Intelligent Matching**: Advanced algorithm that distinguishes between staples (salt, oil) and core ingredients to find the perfect recipe.
- **💎 Premium UI**: A modern, glassmorphic interface designed for a seamless and aesthetically pleasing experience.
- **🔒 Privacy First**: All image processing happens **locally on your machine**. No photos are ever uploaded to the cloud.
- **⚡ High Performance**: Optimized for macOS using **Apple Silicon (MPS)** for lightning-fast inference.

---

## 🛠️ Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python Framework)
- **AI Model**: [Qwen2-VL-2B](https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct) (Vision Language Model)
- **Frontend**: Glassmorphic Vanilla CSS & JavaScript
- **Acceleration**: Metal Performance Shaders (MPS) for Mac GPU support
- **Server**: Uvicorn (ASGI)

---

## 🚀 Getting Started

### Prerequisites

- **OS**: macOS (recommended for MPS acceleration) or Linux/Windows.
- **Python**: 3.9 or higher.
- **Hardware**: 16GB+ RAM recommended for local VLM inference.

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd SmartKitchen.AI
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare the dataset**:
   Ensure your processed recipe dataset is located in the expected directory (refer to [TECHNICAL_OVERVIEW.md](TECHNICAL_OVERVIEW.md) for data structure details).

### Running the Application

Start the FastAPI server:

```bash
python app/main.py
```

The application will be available at `http://localhost:8000`.

---

## ⚙️ Documentation

For a deeper dive into the architecture, model selection, and dataset preprocessing, please see:
- [Technical Overview](TECHNICAL_OVERVIEW.md)
- [Dependency Breakdown](DEPENDENCIES.md)

---

## 🛡️ Privacy & Ownership

By default, SmartKitchen.AI runs entirely offline. This means:
- Your kitchen photos stay on your device.
- No third-party APIs are required (no OpenAI/Gemini tokens).
- Zero cost for image analysis.

---

## 🤝 Contributing

Contributions are welcome! Whether it's improving the matching algorithm, enhancing the UI, or adding new features, feel free to open a Pull Request.

---

*Made with ❤️ for home chefs.*
