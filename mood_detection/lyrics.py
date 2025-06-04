import requests
from bs4 import BeautifulSoup
from utils.config import GENIUS_API_KEY

def get_lyrics(track_name: str, artist_name: str) -> str:
    """
    Fetch lyrics from Genius.com
    Returns: Lyrics text or None if failed
    """
    try:
        # 1. Search Genius for the song
        search_url = "https://api.genius.com/search"
        headers = {"Authorization": f"Bearer {GENIUS_API_KEY}"}
        params = {'q': f"{track_name} {artist_name}"}
        
        search_response = requests.get(search_url, headers=headers, params=params).json()
        
        if not search_response['response']['hits']:
            return None
        
        # 2. Extract the lyrics page URL
        song_path = search_response['response']['hits'][0]['result']['path']
        lyrics_url = f"https://genius.com{song_path}"
        
        # 3. Scrape the actual lyrics
        page = requests.get(lyrics_url)
        soup = BeautifulSoup(page.text, 'html.parser')
        
        # Genius stores lyrics in a div with class "lyrics"
        lyrics_div = soup.find('div', class_='lyrics') or soup.find('div', class_='Lyrics__Container')
        return lyrics_div.get_text(separator='\n') if lyrics_div else None
        
    except Exception as e:
        print(f"⚠️ Lyrics error: {e}")
        return None

def is_happy_lyrics(lyrics: str) -> bool:
    """
    Analyze if lyrics sound happy
    Basic keyword approach (can upgrade to ML later)
    """
    if not lyrics:
        return False
        
    happy_keywords = ['love', 'happy', 'dance', 'joy', 'sunshine', 'smile', 'celebrate']
    sad_keywords = ['sad', 'cry', 'tears', 'lonely', 'hurt', 'miss']
    
    happy_count = sum(lyrics.lower().count(word) for word in happy_keywords)
    sad_count = sum(lyrics.lower().count(word) for word in sad_keywords)
    
    return happy_count > sad_count