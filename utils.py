import pandas as pd
import re
from difflib import SequenceMatcher
from datetime import timedelta
import matplotlib
matplotlib.use("Agg")  # <-- add this
import matplotlib.pyplot as plt
from io import BytesIO
import base64


# ---------- DURATION PARSER ----------
def parse_duration_seconds(iso_duration):
    if not iso_duration:
        return None
    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, iso_duration)
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds

# ---------- CHANNEL RANKING ----------
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def rank_channel_candidates(query, channels):
    ranked = []
    for ch in channels:
        name_score = similarity(query, ch["title"])
        subs_score = min(ch["subscriber_count"] / 1_000_000, 1)
        video_score = min(ch["video_count"] / 1000, 1)
        confidence = round(
            0.5 * name_score +
            0.35 * subs_score +
            0.15 * video_score,
            3
        )
        ranked.append({**ch, "confidence_score": confidence})
    ranked.sort(key=lambda x: x["confidence_score"], reverse=True)
    return ranked

# ---------- SCOPE FILTER ----------
def apply_scope(df, scope):
    if scope == "lifetime":
        return df
    now = pd.Timestamp.now(tz="UTC")
    try:
        days = int(scope.replace("d", ""))
    except:
        return df
    return df[df["publishedAt"] >= now - timedelta(days=days)]

# ---------- METRIC ENGINE ----------
def compute_metrics(df):
    if len(df) < 2:
        return {"insufficient_data": True}
    df = df.sort_values("publishedAt")
    df["gap_days"] = df["publishedAt"].diff().dt.total_seconds() / 86400
    gaps = df["gap_days"].dropna()
    now_utc = pd.Timestamp.now(tz="UTC")
    total_weeks = max((df["publishedAt"].iloc[-1] - df["publishedAt"].iloc[0]).days / 7, 1)
    return {
        "total_videos": len(df),
        "average_gap_days": round(gaps.mean(), 2),
        "median_gap_days": round(gaps.median(), 2),
        "std_dev_gap_days": round(gaps.std(), 2),
        "longest_gap_days": round(gaps.max(), 2),
        "shortest_gap_days": round(gaps[gaps > 0].min(), 2),
        "uploads_last_30_days": df[df["publishedAt"] > now_utc - pd.Timedelta(days=30)].shape[0],
        "active_upload_days": df["publishedAt"].dt.date.nunique(),
        "uploads_per_week": round(len(df) / total_weeks, 2),
        "consistency_score": round(gaps.median() / gaps.mean(), 2) if gaps.mean() > 0 else None,
        "first_upload": df["publishedAt"].iloc[0].strftime("%Y-%m-%d"),
        "latest_upload": df["publishedAt"].iloc[-1].strftime("%Y-%m-%d"),
    }

# ---------- GRAPH GENERATION ----------
def generate_graphs(df):
    graphs = {}
    if len(df) == 0:
        return graphs

    df = df.sort_values("publishedAt")
    df["is_short"] = df["duration_seconds"] <= 60

    # --- Graph 1: Uploads Over Time ---
    daily = df.groupby([df["publishedAt"].dt.date, "is_short"]).size().unstack(fill_value=0)
    plt.figure(figsize=(10,4))
    if False in daily.columns:
        plt.plot(daily.index, daily[False], label="Long-form")
    if True in daily.columns:
        plt.plot(daily.index, daily[True], label="Shorts")
    plt.legend()
    plt.xticks(rotation=45)
    plt.title("Uploads Over Time")
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    graphs["uploads_over_time"] = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()

    # --- Graph 2: Gaps Between Uploads ---
    df["gap_days"] = df["publishedAt"].diff().dt.total_seconds() / 86400
    plt.figure(figsize=(10,4))
    plt.plot(df["publishedAt"][1:], df["gap_days"][1:], marker="o")
    plt.title("Gap Between Uploads (days)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    graphs["gaps_between_uploads"] = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()

    return graphs

# ---------- PUBLIC ANALYTICS ----------
def analyze_periodicity(videos, scope="90d"):
    if len(videos) < 2:
        return {"error": "Not enough videos for analysis"}
    df = pd.DataFrame(videos)
    df["publishedAt"] = pd.to_datetime(df["publishedAt"], utc=True)
    df["duration_seconds"] = df["duration"].apply(parse_duration_seconds)

    df = apply_scope(df, scope)
    if len(df) < 2:
        return {"error": "Not enough videos in selected scope", "scope": scope}

    graphs = generate_graphs(df)

    long_df = df[df["duration_seconds"] > 60]
    short_df = df[df["duration_seconds"] <= 60]

    return {
        "scope": scope,
        "overall": {
            "total_videos": len(df),
            "long_form_videos": len(long_df),
            "short_form_videos": len(short_df)
        },
        "long_form": compute_metrics(long_df),
        "short_form": compute_metrics(short_df),
        "graphs": graphs
    }
