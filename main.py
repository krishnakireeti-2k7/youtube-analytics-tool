from fastapi import FastAPI, Query
from youtube import get_channel_data
from utils import analyze_periodicity

app = FastAPI()


@app.get("/")
def home():
    return {"status": "YouTube Analytics Tool running"}


@app.get("/analytics")
def analytics(channel: str = Query(..., description="YouTube channel name")):
    data, error = get_channel_data(channel)

    if error:
        return {"error": error}

    stats = analyze_periodicity(data["videos"])

    return {
        "channel": data["channel"],
        "analytics": stats
    }
