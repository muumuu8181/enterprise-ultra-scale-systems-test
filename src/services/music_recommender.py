from typing import List, Optional
from src.models.music_models import Track, User, Genre

# Mock data
MOCK_TRACKS = [
    Track(id="1", title="Pop Hit", artist="Star", album="Hits", genre=Genre.POP, bpm=120, key="C", energy=0.8, release_date="2023-01-01", duration=180),
    Track(id="2", title="Rock Anthem", artist="Rocker", album="Rock On", genre=Genre.ROCK, bpm=130, key="D", energy=0.9, release_date="2023-02-01", duration=210),
    Track(id="3", title="Chill Jazz", artist="Jazzy", album="Blue", genre=Genre.JAZZ, bpm=90, key="Bb", energy=0.4, release_date="2023-03-01", duration=240),
    Track(id="4", title="Techno Beat", artist="DJ Tech", album="Rave", genre=Genre.ELECTRONIC, bpm=140, key="Am", energy=0.95, release_date="2023-04-01", duration=300),
    Track(id="5", title="Sad Ballad", artist="Singer", album="Tears", genre=Genre.POP, bpm=80, key="F", energy=0.3, release_date="2023-05-01", duration=195),
]

class MusicRecommender:
    def __init__(self):
        self.tracks = MOCK_TRACKS

    def collaborative_filtering(self, user_id: str) -> List[Track]:
        # Mock: Return popular tracks or random selection
        # In real life: User-Item matrix factorization etc.
        # For mock, simply return high energy tracks as "recommended"
        return [t for t in self.tracks if t.energy > 0.7]

    def audio_feature_similarity(self, track: Track) -> List[Track]:
        # Simple similarity based on BPM and Energy
        similar_tracks = []
        for t in self.tracks:
            if t.id == track.id:
                continue
            bpm_diff = abs(t.bpm - track.bpm)
            energy_diff = abs(t.energy - track.energy)
            if bpm_diff < 30 and energy_diff < 0.3:
                similar_tracks.append(t)
        return similar_tracks

    def generate_radio_queue(self, seed_track_id: str) -> List[Track]:
        seed_track = next((t for t in self.tracks if t.id == seed_track_id), None)
        if not seed_track:
            return []

        queue = [seed_track]
        similar = self.audio_feature_similarity(seed_track)
        queue.extend(similar)
        # Add some randoms if list is short to mimic a radio station
        remaining = [t for t in self.tracks if t.id not in [x.id for x in queue]]
        queue.extend(remaining)

        return queue[:20]

    def update_taste_profile(self, user_id: str, track_id: str, interaction_type: str):
        # Mock: just log or do nothing
        print(f"Updated taste profile for user {user_id} with track {track_id} ({interaction_type})")
        return True
