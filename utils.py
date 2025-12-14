import pandas as pd
import re
from difflib import SequenceMatcher
from datetime import timedelta


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

        ranked.append({
            **ch,
            "confidence_score": confidence
        })

    ranked.sort(key=lambda x: x["confidence_score"], reverse=True)
    return ranked


# ---------- SCOPE FILTER ----------
def parse_scope_to_days(scope):
    if not scope:
        return None

    scope = scope.lower().strip()

    if scope == "lifetime":
        return None

    if scope.endswith("d"):
        scope = scope[:-1]

    try:
        days = int(scope)
        if days <= 0:
            return None
        return days
    except ValueError:
        return None
    
def apply_scope(df, scope):
    days = parse_scope_to_days(scope)

    if days is None:
        return df  # lifetime

    now = pd.Timestamp.now(tz="UTC")
    cutoff = now - timedelta(days=days)

    return df[df["publishedAt"] >= cutoff]



# ---------- METRIC ENGINE ----------
def safe_round(value, ndigits=2):
    if pd.isna(value):
        return None
    return round(float(value), ndigits)


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

    positive_gaps = gaps[gaps > 0]

    mean_gap = gaps.mean()
    median_gap = gaps.median()

    return {
        "total_videos": len(df),

        "average_gap_days": safe_round(mean_gap),
        "median_gap_days": safe_round(median_gap),
        "std_dev_gap_days": safe_round(gaps.std()),

        "longest_gap_days": safe_round(gaps.max()),
        "shortest_gap_days": safe_round(
            positive_gaps.min() if len(positive_gaps) > 0 else None
        ),

        "uploads_last_30_days": df[
            df["publishedAt"] > now_utc - pd.Timedelta(days=30)
        ].shape[0],

        "active_upload_days": int(df["publishedAt"].dt.date.nunique()),
        "uploads_per_week": safe_round(len(df) / total_weeks),

        "consistency_score": safe_round(
            median_gap / mean_gap if mean_gap and mean_gap > 0 else None
        ),

        "first_upload": df["publishedAt"].iloc[0].strftime("%Y-%m-%d"),
        "latest_upload": df["publishedAt"].iloc[-1].strftime("%Y-%m-%d"),
    }


# ---------- PUBLIC ANALYTICS ----------
def analyze_periodicity(videos, scope="90"):
    if len(videos) < 2:
        return {"error": "Not enough videos for analysis"}

    df = pd.DataFrame(videos)

    df["publishedAt"] = pd.to_datetime(df["publishedAt"], utc=True)
    df["duration_seconds"] = df["duration"].apply(parse_duration_seconds)

    # APPLY SCOPE FIRST (CRITICAL)
    df = apply_scope(df, scope)

    if len(df) < 2:
        return {
            "scope": scope,
            "error": "Not enough videos in selected scope"
        }

    df["is_short"] = df["duration_seconds"].apply(
        lambda x: x is not None and x <= 60
    )

    long_df = df[~df["is_short"]]
    short_df = df[df["is_short"]]

    return {
        "scope": scope,

        "overall": {
            "total_videos": len(df),
            "long_form_videos": len(long_df),
            "short_form_videos": len(short_df)
        },

        "long_form": compute_metrics(long_df),
        "short_form": compute_metrics(short_df)
    }
