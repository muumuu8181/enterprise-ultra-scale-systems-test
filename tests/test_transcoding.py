import pytest

def generate_hls_manifest(segments, duration):
    """
    Mock function to generate HLS manifest.
    In a real app, this would be in src/services/transcoding.py
    """
    manifest = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:10\n"
    for i, segment in enumerate(segments):
        manifest += f"#EXTINF:{duration},\n{segment}\n"
    manifest += "#EXT-X-ENDLIST"
    return manifest

def test_hls_manifest_generation():
    segments = ["segment1.ts", "segment2.ts", "segment3.ts"]
    duration = 10

    manifest = generate_hls_manifest(segments, duration)

    assert "#EXTM3U" in manifest
    assert "#EXT-X-VERSION:3" in manifest
    assert "#EXT-X-TARGETDURATION:10" in manifest
    assert "segment1.ts" in manifest
    assert "segment2.ts" in manifest
    assert "segment3.ts" in manifest
    assert "#EXT-X-ENDLIST" in manifest
