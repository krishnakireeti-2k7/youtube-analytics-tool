import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3/"


# ---------- SEARCH CHANNEL ----------
def search_channel(query):
    url = f"{BASE_URL}search"
    params = {
        "part": "snippet",
        "type": "channel",
        "q": query,
        "maxResults": 1,
        "key": API_KEY
    }

    r = requests.get(url, params=params).json()

    if not r.get("items"):
        return None

    return r["items"][0]["snippet"]["channelId"]


# ---------- CHANNEL METADATA ----------
def get_channel_metadata(channel_id):
    url = f"{BASE_URL}channels"
    params = {
        "part": "snippet,statistics,contentDetails",
        "id": channel_id,
        "key": API_KEY
    }

    r = requests.get(url, params=params).json()

    if not r.get("items"):
        return None

    item = r["items"][0]

    return {
        "channel_id": channel_id,
        "title": item["snippet"]["title"],
        "description": item["snippet"].get("description", ""),
        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
        "subscriber_count": int(item["statistics"].get("subscriberCount", 0)),
        "total_views": int(item["statistics"].get("viewCount", 0)),
        "video_count": int(item["statistics"].get("videoCount", 0)),
        "uploads_playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"]
    }


# ---------- PLAYLIST VIDEOS ----------
def get_all_uploaded_videos(uploads_playlist_id):
    videos = []
    url = f"{BASE_URL}playlistItems"

    params = {
        "part": "snippet",
        "playlistId": uploads_playlist_id,
        "maxResults": 50,
        "key": API_KEY
    }

    while True:
        r = requests.get(url, params=params).json()

        for item in r.get("items", []):
            if item["snippet"]["resourceId"]["kind"] != "youtube#video":
                continue

            videos.append({
                "title": item["snippet"]["title"],
                "publishedAt": item["snippet"]["publishedAt"],
                "videoId": item["snippet"]["resourceId"]["videoId"]
            })

        if "nextPageToken" not in r:
            break

        params["pageToken"] = r["nextPageToken"]

    return videos


# ---------- VIDEO DURATIONS ----------
def chunk_list(lst, size=50):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def get_video_durations(video_ids):
    durations = {}
    url = f"{BASE_URL}videos"

    for chunk in chunk_list(video_ids):
        params = {
            "part": "contentDetails",
            "id": ",".join(chunk),
            "key": API_KEY
        }

        r = requests.get(url, params=params).json()

        for item in r.get("items", []):
            durations[item["id"]] = item["contentDetails"]["duration"]

    return durations


# ---------- MAIN ENTRY ----------
def get_channel_data(query):
    channel_id = search_channel(query)
    if not channel_id:
        return None, "Channel not found"

    metadata = get_channel_metadata(channel_id)
    if not metadata:
        return None, "Failed to fetch channel metadata"

    videos = get_all_uploaded_videos(metadata["uploads_playlist_id"])

    video_ids = [v["videoId"] for v in videos]
    durations = get_video_durations(video_ids)

    for v in videos:
        v["duration"] = durations.get(v["videoId"])

    return {
        "channel": metadata,
        "videos": videos
    }, None
