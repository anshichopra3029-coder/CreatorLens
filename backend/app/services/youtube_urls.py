"""Parse public YouTube URLs. This does not fetch or download a video."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse


class YoutubeUrlError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


def parse_youtube_video_id(value: str) -> str:
    text = value.strip()
    if text == "" or len(text) > 500:
        raise YoutubeUrlError("Paste a YouTube video link.")
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise YoutubeUrlError("Paste the full YouTube link, starting with https://")
    host = parsed.hostname.lower().removeprefix("www.")
    video_id = ""
    if host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        parts = [part for part in parsed.path.split("/") if part]
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parts and parts[0] in {"shorts", "embed", "live"} and len(parts) >= 2:
            video_id = parts[1]
        else:
            raise YoutubeUrlError("That YouTube link doesn't point to a single video.")
    elif host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    else:
        raise YoutubeUrlError("That doesn't look like a YouTube video link. Copy the link from the video's Share button.")
    if not _valid_video_id(video_id):
        raise YoutubeUrlError("That link doesn't seem to contain a valid YouTube video. Please check it and try again.")
    return video_id


def canonical_watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def _valid_video_id(video_id: str) -> bool:
    if len(video_id) != 11:
        return False
    return all(character.isalnum() or character in {"-", "_"} for character in video_id)
