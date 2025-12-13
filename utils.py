import pandas as pd
import re


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


# ---------- CORE METRIC ENGINE ----------
def compute_metrics(df):
    if len(df) < 2:
        return {"insufficient_data": True}

    df = df.sort_values("publishedAt")
    df["gap_days"] = df["publishedAt"].diff().dt.total_seconds() / 86400
    gaps = df["gap_days"].dropna()

    now_utc = pd.Timestamp.now(tz="UTC")

    total_weeks = max(
        (df["publishedAt"].iloc[-1] - df["publishedAt"].iloc[0]).days / 7,
        1
    )

    return {
        "total_videos": len(df),

        "average_gap_days": round(gaps.mean(), 2),
        "median_gap_days": round(gaps.median(), 2),
        "std_dev_gap_days": round(gaps.std(), 2),

        "longest_gap_days": round(gaps.max(), 2),
        "shortest_gap_days": round(gaps[gaps > 0].min(), 2),

        "uploads_last_30_days": df[
            df["publishedAt"] > now_utc - pd.Timedelta(days=30)
        ].shape[0],

        "active_upload_days": df["publishedAt"].dt.date.nunique(),
        "uploads_per_week": round(len(df) / total_weeks, 2),

        "consistency_score": round(
            gaps.median() / gaps.mean(), 2
        ) if gaps.mean() > 0 else None,

        "first_upload": df["publishedAt"].iloc[0].strftime("%Y-%m-%d"),
        "latest_upload": df["publishedAt"].iloc[-1].strftime("%Y-%m-%d"),
    }


# ---------- PUBLIC ANALYTICS API ----------
def analyze_periodicity(videos):
    if len(videos) < 2:
        return {"error": "Not enough videos for analysis"}

    df = pd.DataFrame(videos)

    df["publishedAt"] = pd.to_datetime(df["publishedAt"], utc=True)
    df["duration_seconds"] = df["duration"].apply(parse_duration_seconds)

    # YouTube Shorts definition
    df["is_short"] = df["duration_seconds"].apply(
        lambda x: x is not None and x <= 60
    )

    long_df = df[~df["is_short"]]
    short_df = df[df["is_short"]]

    return {
        "overall": {
            "total_videos": len(df),
            "long_form_videos": len(long_df),
            "short_form_videos": len(short_df),
        },

        "long_form": compute_metrics(long_df),
        "short_form": compute_metrics(short_df),
    }
