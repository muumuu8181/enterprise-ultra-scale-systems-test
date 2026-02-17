from src.services.cdn_manager import CDNManager

def test_cdn_manager():
    cdn = CDNManager()
    assert cdn.invalidate_cache("http://example.com") is True
    assert cdn.get_optimal_cdn_url("us-east") == "https://us-east.cdn.example.com"
    assert cdn.get_optimal_cdn_url("unknown") == "https://global.cdn.example.com"
    assert cdn.prefetch_popular_videos(["vid1", "vid2"]) is True
