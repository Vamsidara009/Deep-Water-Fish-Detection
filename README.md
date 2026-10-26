<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/YOLO-v8%20|%20v9%20|%20v10%20|%20v11%20|%20v12-00FFFF?style=for-the-badge" />
  <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" />
</p>

<h1 align="center">🌊 DeepSea Fish Detection & Tracking AI</h1>

<p align="center">
  <b>Real-time deep-sea fish detection, tracking, and population counting powered by YOLO and multiple tracking algorithms — served through a sleek web dashboard.</b>
</p>

---

## 🎯 Overview

This project provides an end-to-end system for **detecting, tracking, and counting deep-sea fish** in underwater video footage. It combines state-of-the-art object detection (YOLO family) with robust multi-object tracking algorithms to deliver accurate population counts in real-time through a beautiful web-based dashboard.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔍 **Multi-Model Support** | Switch between YOLOv8, YOLOv9, YOLOv10, YOLO11, YOLO12, and custom-trained models |
| 🎯 **Multiple Trackers** | BoT-SORT, BYTETracker, DeepSORT, and Occlusion-Tuned BoT-SORT |
| 📊 **Live Dashboard** | Real-time stats — fish count, FPS, processed frames, and population graph |
| 🖼️ **Image Preprocessing** | CLAHE enhancement + Grey World White Balance for murky underwater footage |
| 📹 **Flexible Input** | Upload custom MP4 videos or use built-in sample clips |
| 🔧 **Configurable** | Adjustable confidence threshold, model selection, and tracker switching on-the-fly |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Browser (Frontend)                 │
│  ┌─────────┐  ┌───────────┐  ┌────────────────────┐ │
│  │ Controls │  │ Video Feed│  │ Stats + Chart.js   │ │
│  └────┬────┘  └─────┬─────┘  └─────────┬──────────┘ │
│       │             │                   │            │
└───────┼─────────────┼───────────────────┼────────────┘
        │             │                   │
   POST /upload  GET /video_feed    GET /stats
        │             │                   │
┌───────┼─────────────┼───────────────────┼────────────┐
│       ▼             ▼                   ▼            │
│              FastAPI Backend (main.py)               │
│  ┌──────────┐  ┌───────────┐  ┌────────────────┐    │
│  │ YOLO     │  │ Tracker   │  │ Frame          │    │
│  │ Detector │──│ (BoTSORT/ │──│ Enhancement    │    │
│  │          │  │ DeepSORT) │  │ (CLAHE + WB)   │    │
│  └──────────┘  └───────────┘  └────────────────┘    │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/ansul01/deep-water_fish_detection.git
cd deep-water_fish_detection

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Adding Model Weights

Download your YOLO model weights (`.pt` files) and place them in the `models/` directory:

```
models/
├── best.pt            # Custom-trained model
├── yolov8n.pt         # YOLOv8 Nano
├── yolov8x.pt         # YOLOv8 Extra Large
├── yolov9c.pt         # YOLOv9 Compact
├── yolov10n.pt        # YOLOv10 Nano
├── yolo11n.pt         # YOLO11 Nano
├── yolo12n.pt         # YOLO12 Nano
├── yolo12s.pt         # YOLO12 Small
├── yolo12m.pt         # YOLO12 Medium
├── yolo12l.pt         # YOLO12 Large
└── yolo12x.pt         # YOLO12 Extra Large
```

> 💡 Models are lazy-loaded — only the selected model is loaded into memory.

### Running the App

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open your browser and navigate to **http://localhost:8000**

---

## 🖥️ Usage

1. **Select a Tracking Algorithm** — Choose from BoT-SORT, BYTETracker, DeepSORT, or Occlusion-Tuned BoT-SORT
2. **Pick a Detection Model** — All `.pt` models in the `models/` folder are auto-discovered
3. **Set Confidence Threshold** — Use the slider to adjust detection sensitivity (0.1 – 1.0)
4. **Toggle Image Preprocessing** — Enable CLAHE + White Balance for low-visibility footage
5. **Upload or Select a Video** — Upload a custom MP4 or pick from sample videos
6. **Start Analysis** — Hit the button and watch the live feed with bounding boxes, IDs, and real-time stats

---

## 🔬 Image Enhancement Pipeline

The preprocessing module (`utils.py`) applies two techniques to improve detection in challenging underwater conditions:

1. **CLAHE (Contrast Limited Adaptive Histogram Equalization)**
   - Applied in LAB color space on the L (lightness) channel
   - Clip limit: 2.0 | Tile grid: 8×8
   - Enhances local contrast without amplifying noise

2. **Grey World White Balance**
   - Corrects color casts common in deep-sea footage
   - Normalizes each channel to the global average intensity

---

## 📁 Project Structure

```
deep-water_fish_detection/
├── main.py                    # FastAPI application & detection pipeline
├── utils.py                   # Image enhancement & centroid tracker
├── requirements.txt           # Python dependencies
├── occlusion_botsort.yaml     # Custom BoT-SORT tracker config
├── static/
│   ├── index.html             # Web dashboard UI
│   ├── style.css              # Glassmorphism-styled CSS
│   └── script.js              # Frontend logic & Chart.js integration
├── models/                    # YOLO weight files (.pt) — not tracked in git
├── sample_inputs/             # Sample underwater video clips
├── sample_outputs/            # Pre-generated output videos
└── uploads/                   # User-uploaded videos (runtime)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, Uvicorn |
| **Detection** | Ultralytics YOLO (v8 / v9 / v10 / v11 / v12) |
| **Tracking** | BoT-SORT, BYTETracker, DeepSORT, BoxMOT |
| **Vision** | OpenCV, NumPy |
| **Frontend** | HTML5, CSS3 (Glassmorphism), JavaScript, Chart.js |
| **Streaming** | MJPEG over HTTP (multipart/x-mixed-replace) |

---

## 📄 License

This project is developed as an academic minor project. Feel free to use and modify for educational purposes.

---

<p align="center">
  Made with 🐟 by <a href="https://github.com/ansul01">ansul01</a>
</p>
