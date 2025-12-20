from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from youtube import resolve_channel, get_channel_videos
from utils import analyze_periodicity, rank_channel_candidates

app = FastAPI(title="YouTube Analytics Tool")

# --------------------------------------------------
# CORS (required for Next.js frontend)
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Health check
# --------------------------------------------------
@app.get("/")
def health():
    return {"status": "ok"}

# --------------------------------------------------
# Analytics endpoint
# --------------------------------------------------
@app.get("/analytics")
def analytics(
    channel: str = Query(..., description="Channel name or handle"),
    scope: str = Query(
        "90d",
        description="Analysis scope: 30d, 90d, 180d, 365d, lifetime"
    ),
    auto_select: bool = Query(
        True,
        description="Auto-pick best channel if ambiguity exists"
    )
):
    # 1. Resolve channel ambiguity
    candidates, error = resolve_channel(channel)
    if error:
        return {"error": error}
    
    # 2. Rank candidates
    ranked = rank_channel_candidates(channel, candidates)

    # 3. Auto-pick best channel
    selected = ranked[0]

    if not auto_select and selected["confidence_score"] < 0.85:
        return {
            "ambiguous": True,
            "candidates": ranked
        }

    # 4. Fetch videos
    videos = get_channel_videos(selected)

    # 5. Run analytics (scope-aware)
    analytics_data = analyze_periodicity(videos, scope=scope)

    return {
        "channel": selected,
        "analytics": analytics_data
    }
