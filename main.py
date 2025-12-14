from fastapi import FastAPI, Query
from youtube import resolve_channel, get_channel_videos
from utils import analyze_periodicity, rank_channel_candidates

app = FastAPI()


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/analytics")
def analytics(
    channel: str = Query(..., description="Channel name"),
    auto_select: bool = True
):
    # 1. Resolve channel ambiguity
    candidates, error = resolve_channel(channel)
    if error:
        return {"error": error}

    # 2. Rank candidates
    ranked = rank_channel_candidates(channel, candidates)

    # 3. Auto-pick best channel (safe default)
    selected = ranked[0]

    if not auto_select and selected["confidence_score"] < 0.85:
        return {
            "ambiguous": True,
            "candidates": ranked
        }

    # 4. Fetch videos
    videos = get_channel_videos(selected)

    # 5. Run analytics
    analytics = analyze_periodicity(videos)

    return {
        "channel": selected,
        "analytics": analytics
    }
