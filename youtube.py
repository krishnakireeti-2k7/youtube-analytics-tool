import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

BASE_URL = "https://www.googleapis.com/youtube/v3/"


def search_channel(query):
    url = f"{BASE_URL}search?part=snippet&type=channel&q={query}&key={API_KEY}"
    r = requests.get(url).json()

    if "items" not in r or len(r["items"]) == 0:
        return None

    return r["items"][0]["snippet"]["channelId"]


def get_uploads_playlist(channel_id):
    url = f"{BASE_URL}channels?part=contentDetails&id={channel_id}&key={API_KEY}"
    r = requests.get(url).json()

    try:
        return r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except:
        return None


def get_all_uploaded_videos(uploads_playlist_id):
    url = f"{BASE_URL}playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=50&key={API_KEY}"

    videos = []
    r = requests.get(url).json()

    while True:
        for item in r.get("items", []):
            videos.append({
                "title": item["snippet"]["title"],
                "publishedAt": item["snippet"]["publishedAt"],
                "videoId": item["snippet"]["resourceId"]["videoId"]
            })

        if "nextPageToken" in r:
            next_page = r["nextPageToken"]
            url = f"{BASE_URL}playlistItems?part=snippet&playlistId={uploads_playlist_id}&maxResults=50&pageToken={next_page}&key={API_KEY}"
            r = requests.get(url).json()
        else:
            break

    return videos


def get_channel_videos(query):
    channel_id = search_channel(query)
    if not channel_id:
        return None, "Channel not found"

    uploads_playlist_id = get_uploads_playlist(channel_id)
    if not uploads_playlist_id:
        return None, "Uploads playlist not found"

    videos = get_all_uploaded_videos(uploads_playlist_id)
    return videos, None
