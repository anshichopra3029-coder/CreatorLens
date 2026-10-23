const VIDEO_ID = /^[A-Za-z0-9_-]{11}$/;

export function parseYoutubeVideoId(value: string): string {
  const text = value.trim();
  if (text === "" || text.length > 500) {
    throw new Error("Paste a YouTube video link.");
  }
  let parsed: URL;
  try {
    parsed = new URL(text);
  } catch {
    throw new Error("Paste the full YouTube link, starting with https://");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("Paste the full YouTube link, starting with https://");
  }
  const host = parsed.hostname.toLowerCase().replace(/^www\./, "");
  let videoId = "";
  if (host === "youtube.com" || host === "m.youtube.com" || host === "music.youtube.com") {
    const parts = parsed.pathname.split("/").filter(Boolean);
    if (parsed.pathname === "/watch") {
      videoId = parsed.searchParams.get("v") ?? "";
    } else if (parts.length >= 2 && (parts[0] === "shorts" || parts[0] === "embed" || parts[0] === "live")) {
      videoId = parts[1] ?? "";
    } else {
      throw new Error("That YouTube link doesn't point to a single video.");
    }
  } else if (host === "youtu.be") {
    videoId = parsed.pathname.replace(/^\/+/, "").split("/")[0] ?? "";
  } else {
    throw new Error("That doesn't look like a YouTube video link. Copy the link from the video's Share button.");
  }
  if (!VIDEO_ID.test(videoId)) {
    throw new Error("That link doesn't seem to contain a valid YouTube video. Please check it and try again.");
  }
  return videoId;
}
