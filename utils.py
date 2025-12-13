import pandas as pd
import numpy as np
import re


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


def analyze_periodicity(videos, use_long_form_only=True):
    if len(videos) < 2:
        return {"error": "Not enough videos for analysis"}

    df = pd.DataFrame(videos)

    # Parse timestamps (UTC-aware)
    df["publishedAt"] = pd.to_datetime(df["publishedAt"], utc=True)

    # Parse duration
    df["duration_seconds"] = df["duration"].apply(parse_duration_seconds)

    # Shorts = <= 60 seconds (YouTube definition)
    df["is_short"] = df["duration_seconds"].apply(
        lambda x: x is not None and x <= 60
    )

    long_df = df[~df["is_short"]]
    short_df = df[df["is_short"]]

    used_df = long_df if use_long_form_only and len(long_df) >= 2 else df
    used_label = "long_form_only" if used_df is long_df else "all_videos"

    used_df = used_df.sort_values("publishedAt")

    # Gap calculation (days)
    used_df["gap_days"] = used_df["publishedAt"].diff().dt.total_seconds() / 86400
    gaps = used_df["gap_days"].dropna()

    now_utc = pd.Timestamp.now(tz="UTC")

    # Active upload days
    active_days = used_df["publishedAt"].dt.date.nunique()

    # Weekly upload frequency
    total_weeks = max(
        (used_df["publishedAt"].iloc[-1] - used_df["publishedAt"].iloc[0]).days / 7,
        1
    )
    uploads_per_week = round(len(used_df) / total_weeks, 2)

    # Consistency score
    consistency_score = round(
        gaps.median() / gaps.mean(), 2
    ) if gaps.mean() > 0 else None

    return {
        "total_videos": len(df),
        "long_form_videos": len(long_df),
        "short_form_videos": len(short_df),

        "average_gap_days": round(gaps.mean(), 2),
        "median_gap_days": round(gaps.median(), 2),
        "std_dev_gap_days": round(gaps.std(), 2),

        "longest_gap_days": round(gaps.max(), 2),
        "shortest_gap_days": round(gaps[gaps > 0].min(), 2),

        "uploads_last_30_days_total": df[df["publishedAt"] > now_utc - pd.Timedelta(days=30)].shape[0],
        "uploads_last_30_days_long_form": long_df[long_df["publishedAt"] > now_utc - pd.Timedelta(days=30)].shape[0],
        "uploads_last_30_days_shorts": short_df[short_df["publishedAt"] > now_utc - pd.Timedelta(days=30)].shape[0],

        "active_upload_days": active_days,
        "uploads_per_week": uploads_per_week,
        "consistency_score": consistency_score,

        "first_upload": used_df["publishedAt"].iloc[0].strftime("%Y-%m-%d"),
        "latest_upload": used_df["publishedAt"].iloc[-1].strftime("%Y-%m-%d"),

        "used_for_periodicity": used_label
    }
