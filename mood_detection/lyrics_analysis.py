import requests
from textblob import TextBlob
from spotify_integration.auth import get_spotify_client

def get_lyrics_sentiment(track_id):
    """Analyze lyrics using Genius API"""
    sp = get_spotify_client()
    
    try:
        # Get track info
        track = sp.track(track_id)
        artist = track['artists'][0]['name']
        title = track['name']
        
        # Search Genius for lyrics (you'll need a Genius API key)
        genius_url = f"https://api.genius.com/search?q={artist} {title}"
        headers = {"Authorization": "Bearer YOUR_GENIUS_API_KEY"}
        response = requests.get(genius_url, headers=headers).json()
        
        if response['response']['hits']:
            lyrics_url = response['response']['hits'][0]['result']['url']
            # Here you would scrape/extract the actual lyrics
            # Then analyze sentiment:
            lyrics = "..."  # Extract lyrics from URL
            analysis = TextBlob(lyrics)
            return analysis.sentiment.polarity  # -1 to 1 scale
    except:
        return None

def is_happy_song(track_id, threshold=0.3):
    sentiment = get_lyrics_sentiment(track_id)
    return sentiment and sentiment > threshold