from typing import Dict, List, Optional
import random

class VideoProcessor:
    def transcode_video(self, file_url: str) -> Dict[str, str]:
        """
        Mocks FFmpeg transcoding.
        Returns a dictionary of resolution to HLS playlist URL.
        """
        # Mock processing time or logic could be added here
        base_name = file_url.split('/')[-1].split('.')[0]
        return {
            "720p": f"https://cdn.example.com/hls/{base_name}_720p.m3u8",
            "1080p": f"https://cdn.example.com/hls/{base_name}_1080p.m3u8",
            "4k": f"https://cdn.example.com/hls/{base_name}_4k.m3u8"
        }

    def generate_thumbnail(self, video_id: int) -> str:
        """
        Generates a thumbnail for the video.
        Returns a URL to the thumbnail.
        """
        return f"https://cdn.example.com/thumbnails/{video_id}.jpg"

    def extract_subtitles(self, video_id: int) -> str:
        """
        Extracts subtitles from the video.
        Returns the subtitle content as a string (e.g., VTT or SRT format).
        """
        return "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nHello world!"

    def detect_content_policy_violations(self, title: str, description: str) -> bool:
        """
        Detects content policy violations based on title and description.
        Returns True if a violation is detected, False otherwise.
        """
        forbidden_keywords = ["spam", "violence", "hate speech"]
        text = (title + " " + description).lower()
        for keyword in forbidden_keywords:
            if keyword in text:
                return True
        return False
