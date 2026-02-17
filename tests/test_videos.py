from src.models.video_models import Video, VideoStatus

def test_upload_video(client):
    response = client.post("/videos/upload", json={
        "title": "My Cat Video",
        "description": "Cute cat playing with yarn",
        "file_url": "http://example.com/cat.mp4"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "My Cat Video"
    assert data["status"] == "ready"
    assert data["hls_url"] is not None
    assert data["thumbnail_url"] is not None

def test_upload_video_policy_violation(client):
    response = client.post("/videos/upload", json={
        "title": "spam video",
        "description": "buy my product",
        "file_url": "http://example.com/spam.mp4"
    })
    assert response.status_code == 400
    assert "policy violation" in response.json()["detail"]

def test_get_video(client, db_session):
    # Setup
    video = Video(
        creator_id=1,
        title="Test Video",
        description="Test Desc",
        status=VideoStatus.READY.value,
        hls_url="http://hls",
        thumbnail_url="http://thumb"
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)

    response = client.get(f"/videos/{video.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Video"
    assert data["views"] == 1  # Incremented on view

def test_like_video(client, db_session):
    # Setup
    video = Video(
        creator_id=1,
        title="Test Video",
        description="Test Desc",
        status=VideoStatus.READY.value
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)

    response = client.post(f"/videos/{video.id}/like")
    assert response.status_code == 200
    assert response.json()["likes"] == 1

def test_trending_videos(client, db_session):
    # Setup
    v1 = Video(creator_id=1, title="V1", status=VideoStatus.READY.value, views=10)
    v2 = Video(creator_id=1, title="V2", status=VideoStatus.READY.value, views=20)
    db_session.add_all([v1, v2])
    db_session.commit()

    response = client.get("/videos/trending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "V2"  # Higher views first
    assert data[1]["title"] == "V1"

def test_search_videos(client, db_session):
    # Setup
    v1 = Video(creator_id=1, title="Python Tutorial", description="Learn coding", status=VideoStatus.READY.value)
    v2 = Video(creator_id=1, title="Cooking Show", description="Learn cooking", status=VideoStatus.READY.value)
    db_session.add_all([v1, v2])
    db_session.commit()

    response = client.get("/videos/search?q=Python")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Python Tutorial"
