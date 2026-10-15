const VIDEO_ID = /^[A-Za-z0-9_-]{11}$/;

export function parseYoutubeVideoId(value: string): string {
  const text = value.trim();
  if (text === "" || text.length > 500) {
    throw new Error("Paste a YouTube video URL.");
  }
  let parsed: URL;
  try {
    parsed = new URL(text);
  } catch {
    throw new Error("Paste a full http or https YouTube URL.");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("Paste a full http or https YouTube URL.");
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
      throw new Error("That YouTube URL does not point at one video.");
    }
  } else if (host === "youtu.be") {
    videoId = parsed.pathname.replace(/^\/+/, "").split("/")[0] ?? "";
  } else {
    throw new Error("Only YouTube watch, youtu.be, Shorts, embed, and live URLs are supported.");
  }
  if (!VIDEO_ID.test(videoId)) {
    throw new Error("That URL does not contain a valid YouTube video ID.");
  }
  return videoId;
}
