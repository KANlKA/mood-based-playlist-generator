from spotify_integration.auth import get_spotify_client
import datetime

def create_mood_playlist(user_id: str, playlist_name: str, tracks: list):
    """
    Create a new Spotify playlist with the given tracks
    
    Args:
        user_id: Spotify user ID
        playlist_name: Name for the playlist
        tracks: List of track objects
    
    Returns:
        Created playlist object
    """
    sp = get_spotify_client()
    
    today = datetime.datetime.now().strftime("%b %d")
    full_playlist_name = f"{playlist_name} - {today}"
    
    description = f"Created by Mood-Based Playlist Generator on {today}"
    
    try:
        playlist = sp.user_playlist_create(
            user=user_id,
            name=full_playlist_name,
            public=True,
            description=description
        )
    
        if tracks:
            track_uris = [track['uri'] for track in tracks]
        
            for i in range(0, len(track_uris), 100):
                batch = track_uris[i:i+100]
                sp.playlist_add_items(playlist_id=playlist['id'], items=batch)
        
        return playlist
    
    except Exception as e:
        print(f"Error creating playlist: {e}")
        raise