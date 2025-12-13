import pandas as pd
import numpy as np

def analyze_periodicity(videos):
    if len(videos) < 2:
        return {"error": "Not enough videos for periodicity analysis"}

    df = pd.DataFrame(videos)

    # Parse timestamps as UTC-aware
    df["publishedAt"] = pd.to_datetime(df["publishedAt"], utc=True)

    df = df.sort_values("publishedAt")

    # Gap between uploads (in days)
    df["gap_days"] = df["publishedAt"].diff().dt.total_seconds() / 86400
    gaps = df["gap_days"].dropna()

    # Current time in UTC (timezone-aware)
    now_utc = pd.Timestamp.now(tz="UTC")

    return {
        "total_videos": len(videos),
        "average_gap_days": round(gaps.mean(), 2),
        "std_dev_gap_days": round(gaps.std(), 2),
        "longest_gap_days": round(gaps.max(), 2),
        "shortest_gap_days": round(gaps.min(), 2),
        "uploads_last_30_days": df[df["publishedAt"] > now_utc - pd.Timedelta(days=30)].shape[0],
        "first_upload": df["publishedAt"].iloc[0].strftime("%Y-%m-%d"),
        "latest_upload": df["publishedAt"].iloc[-1].strftime("%Y-%m-%d"),
        "upload_dates": df["publishedAt"].dt.strftime("%Y-%m-%d").tolist()
    }
