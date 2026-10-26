import os
import cv2
import uuid
import time
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

from utils import enhance_frame

app = FastAPI(title="DeepSea Fish Detection")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Lazy load models to save RAM
models_dict = {}

def get_model(model_name: str):
    if model_name not in models_dict:
        path = f"models/{model_name}"
        if os.path.exists(path):
            try:
                print(f"Loading model {model_name}...")
                models_dict[model_name] = YOLO(path)
                print(f"Successfully loaded {model_name}")
            except Exception as e:
                print(f"Error loading model {model_name}: {e}")
                return None
        else:
            print(f"WARNING: {path} not found!")
            return None
    return models_dict.get(model_name)

# Global store for stream info
stream_stats = {}
active_streams = {}

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload")
async def upload_video(file: UploadFile = File(None), sample_video: str = Form(None), tracker: str = Form("botsort.yaml"), conf: float = Form(0.25), model_type: str = Form("yolo"), enhance: str = Form(None)):
    stream_id = str(uuid.uuid4())
    video_path = None

    if file and file.filename:
        # Save uploaded file
        os.makedirs("uploads", exist_ok=True)
        video_path = f"uploads/{stream_id}.mp4"
        with open(video_path, "wb") as f:
            content = await file.read()
            f.write(content)
    elif sample_video:
        video_path = f"sample_inputs/{sample_video}"
    
    if not video_path or not os.path.exists(video_path):
        return JSONResponse(status_code=400, content={"error": "No valid video provided or found."})

    active_streams[stream_id] = {
        "path": video_path,
        "tracker": tracker,
        "conf": conf,
        "model_type": model_type,
        "enhance": enhance == "true",
        "active": True
    }
    stream_stats[stream_id] = {"count": 0, "fps": 0, "frames": 0, "history": []}

    return {"stream_id": stream_id}


def generate_frames(stream_id: str):
    info = active_streams.get(stream_id)
    if not info:
        return

    cap = cv2.VideoCapture(info["path"])
    tracker_type = info["tracker"]
    conf = float(info["conf"])
    model_type = info.get("model_type", "yolo")

    counted_ids = set()
    track_lengths = {}
    frame_num = 0

    deepsort_tracker = None
    if tracker_type == "deepsort":
        deepsort_tracker = DeepSort(max_age=30, n_init=3)

    start_time = time.time()



    while cap.isOpened() and info.get("active", False):
        try:
            ret, frame = cap.read()
            if not ret:
                break

            # Resize for performance and consistency
            frame = cv2.resize(frame, (640, 640))
            
            # Apply enhancements
            if info.get("enhance"):
                frame = enhance_frame(frame)



            boxes_xyxy = []
            track_ids = []

            active_model = get_model(model_type)

            if active_model:
                if tracker_type == "deepsort" and deepsort_tracker is not None:
                    # Run standard YOLO detection (predict, not track)
                    results = active_model.predict(frame, conf=conf, verbose=False)
                    if results and len(results) > 0:
                        res = results[0]
                        # Convert to DeepSORT format: ([x,y,w,h], confidence, class)
                        bbs = []
                        if getattr(res, 'boxes', None) is not None:
                            for box in res.boxes:
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                c = box.conf[0].cpu().item()
                                cls = box.cls[0].cpu().item()
                                bbs.append(([x1, y1, x2 - x1, y2 - y1], c, int(cls)))
                        
                        # Update DeepSORT
                        tracks = deepsort_tracker.update_tracks(bbs, frame=frame)
                        
                        # Extract back to boxes_xyxy and track_ids format
                        for track in tracks:
                            if not track.is_confirmed():
                                continue
                            tid = track.track_id
                            ltrb = track.to_ltrb() # left, top, right, bottom
                            boxes_xyxy.append(ltrb)
                            track_ids.append(int(tid))
                else:
                    # Run standard YOLO detection and tracking
                    results = active_model.track(frame, conf=conf, persist=True, tracker=tracker_type, verbose=False)
                    if results and len(results) > 0 and getattr(results[0], 'boxes', None) is not None:
                        boxes_xyxy = results[0].boxes.xyxy.cpu().numpy()
                        track_ids = results[0].boxes.id.int().cpu().tolist() if getattr(results[0].boxes, 'id', None) is not None else [None] * len(boxes_xyxy)
                    


            # Draw results
            for box, tid in zip(boxes_xyxy, track_ids):
                x1, y1, x2, y2 = map(int, box)

                if tid is not None:
                    # Increment track length for this ID
                    track_lengths[tid] = track_lengths.get(tid, 0) + 1

                    # Count the fish if it has been tracked for > 5 frames
                    if track_lengths[tid] > 5 and tid not in counted_ids:
                        counted_ids.add(tid)

                    label = f"ID {tid}"
                    color = (0, 255, 0)
                else:
                    label = "No ID"
                    color = (0, 165, 255)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Update stats
            frame_num += 1
            elapsed_time = time.time() - start_time
            fps = frame_num / elapsed_time if elapsed_time > 0 else 0
            count = len(counted_ids)
            
            stream_stats[stream_id]["count"] = count
            stream_stats[stream_id]["fps"] = fps
            stream_stats[stream_id]["frames"] = frame_num
            stream_stats[stream_id]["history"].append(count)
            # Keep history from growing too large (e.g. 50 points max)
            if len(stream_stats[stream_id]["history"]) > 50:
                stream_stats[stream_id]["history"].pop(0)

            # Overlay simple count on frame as well
            cv2.putText(frame, f"Count: {len(counted_ids)}", (20, 45), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Encode and yield
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Add slight delay to prevent overwhelming the browser
            time.sleep(0.01)
        except Exception as e:
            import traceback
            print("Error in generator loop:", e)
            traceback.print_exc()
            break

    cap.release()
    info["active"] = False


@app.get("/video_feed/{stream_id}")
async def video_feed(stream_id: str):
    return StreamingResponse(generate_frames(stream_id), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/stats/{stream_id}")
async def get_stats(stream_id: str):
    stats = stream_stats.get(stream_id, {"count": 0, "fps": 0, "frames": 0, "history": []})
    active = active_streams.get(stream_id, {}).get("active", False)
    return JSONResponse({"stats": stats, "active": active})


@app.get("/samples")
async def list_samples():
    samples_dir = "sample_inputs"
    if not os.path.exists(samples_dir):
        return []
    samples = [f for f in os.listdir(samples_dir) if f.endswith('.mp4')]
    return samples

@app.get("/models")
async def list_models():
    models_dir = "models"
    if not os.path.exists(models_dir):
        return []
    models = [f for f in os.listdir(models_dir) if f.endswith('.pt')]
    return models

@app.post("/stop/{stream_id}")
async def stop_stream(stream_id: str):
    if stream_id in active_streams:
        active_streams[stream_id]["active"] = False
    return {"status": "stopped"}
