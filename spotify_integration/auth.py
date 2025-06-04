import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
import os

def get_spotify_client():
    """
    Authenticate and return Spotify client with caching
    
    Returns:
        Authenticated Spotipy client
    Raises:
        Exception: If authentication fails
    """
    scope = " ".join([
    "user-library-read",   
    "user-top-read",           
    "playlist-modify-public", 
    "user-read-private",       
    "user-read-email",   
    "user-read-playback-state", 
    "user-modify-playback-state" 
])
    
    try:
        cache_path = ".spotify_cache"
        os.makedirs(cache_path, exist_ok=True)
        
        return spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=scope,
            cache_path=os.path.join(cache_path, "token_cache"),
            show_dialog=True  
        ))
    except Exception as e:
        print(f"Failed to authenticate with Spotify: {e}")
        raise