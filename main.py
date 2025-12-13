from fastapi import FastAPI
from youtube import get_channel_videos
from utils import analyze_periodicity

app = FastAPI()

@app.get("/")
def root():
    return {"message": "YouTube Analytics API Running"}

@app.get("/analytics")
def analytics(channel: str):
    videos, err = get_channel_videos(channel)

    if err:
        return {"error": err}

    stats = analyze_periodicity(videos)
    return stats
