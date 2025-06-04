from spotify_integration.search import get_tracks_by_mood
from spotify_integration.playlists import create_mood_playlist
from utils.config import SPOTIFY_USER_ID
import streamlit as st

language_codes = {
    'English': 'en',
    'Spanish': 'es',
    'French': 'fr',
    'Hindi': 'hi',
    'Korean': 'ko',
}

mood_options = {
    "happy": "😊 Happy",
    "sad": "😢 Sad",
    "angry": "😠 Angry",
    "calm": "😌 Calm"
}

def analyze_feeling_text(feeling_text):
    feeling_text = feeling_text.lower()
    
    happy_keywords = ["happy", "joy", "excited", "energetic", "upbeat", "cheerful", 
                      "good", "great", "wonderful", "positive", "uplifted", "enthusiastic"]
    
    sad_keywords = ["sad", "down", "blue", "depressed", "unhappy", "somber", "melancholic", 
                    "gloomy", "heartbroken", "disappointed", "upset", "lonely", "miserable"]
    
    angry_keywords = ["angry", "mad", "furious", "rage", "upset", "frustrated", "annoyed", 
                      "irritated", "outraged", "hostile", "bitter", "enraged"]
    
    calm_keywords = ["calm", "peaceful", "relaxed", "chill", "tranquil", "serene", 
                     "content", "zen", "soothing", "mellow", "quiet", "gentle"]
    
    for word in feeling_text.split():
        if word in happy_keywords:
            return "happy"
        elif word in sad_keywords:
            return "sad"
        elif word in angry_keywords:
            return "angry"
        elif word in calm_keywords:
            return "calm"
    
    for keyword in happy_keywords:
        if keyword in feeling_text:
            return "happy"
    for keyword in sad_keywords:
        if keyword in feeling_text:
            return "sad"
    for keyword in angry_keywords:
        if keyword in feeling_text:
            return "angry"
    for keyword in calm_keywords:
        if keyword in feeling_text:
            return "calm"
    
    return "calm"

def main():
    st.title("Mood-Based Playlist Generator")
    st.write("Create personalized playlists with one click!")
    
    selected_language = st.selectbox(
        "Choose your preferred language:",
        list(language_codes.keys()),
        index=0
    )
    language_code = language_codes[selected_language]
    
    st.subheader("2. Select Your Mood")
    
    cols = st.columns(4)
    selected_mood = None
    
    for i, (mood_key, mood_display) in enumerate(mood_options.items()):
        with cols[i]:
            if st.button(mood_display, key=f"mood_{mood_key}"):
                selected_mood = mood_key
    
    st.write("Or describe how you're feeling:")
    feeling_text = st.text_input(
        "How are you feeling today?",
        placeholder="I'm feeling...",
        key="feeling_text"
    )
    
    if feeling_text:
        detected_mood = analyze_feeling_text(feeling_text)
        st.info(f"Based on your description, we think you might be feeling: {mood_options[detected_mood]}")
        if selected_mood is None:
            selected_mood = detected_mood
    
    if selected_mood is None:
        selected_mood = st.radio(
            "Or select your mood:",
            list(mood_options.keys()),
            format_func=lambda x: mood_options[x],
            index=0
        )
    else:
        st.success(f"Selected: {mood_options[selected_mood]}")
    
    st.subheader("3. Customize Your Playlist")
    
    playlist_size = st.slider(
        "Number of tracks:",
        min_value=5,
        max_value=50,
        value=20,
        step=5
    )
    
    custom_name = st.text_input(
        "Custom name (optional):",
        placeholder=f"My {selected_mood.title()} {selected_language} Mix"
    )
    
    if st.button("🎵 Generate Playlist", type="primary"):
        with st.spinner(f"Creating your {selected_mood} playlist..."):
            try:
                tracks = get_tracks_by_mood(selected_mood, language_code, playlist_size)
                
                if not tracks:
                    st.error("Couldn't find matching tracks. Try different settings.")
                    return
                
                playlist_name = custom_name or f"{mood_options[selected_mood]} {selected_language} Mix"
                
                if feeling_text and not custom_name:
                    short_feeling = feeling_text[:20] + "..." if len(feeling_text) > 20 else feeling_text
                    playlist_name = f"{short_feeling} - {playlist_name}"
                
                playlist = create_mood_playlist(SPOTIFY_USER_ID, playlist_name, tracks)
                
                st.success(f"✅ Playlist created!")
                st.markdown(
                    f'<a href="{playlist["external_urls"]["spotify"]}" target="_blank" '
                    'style="background-color: #1DB954; color: white; padding: 10px 20px; '
                    'border-radius: 30px; text-decoration: none; font-weight: bold;">'
                    '🎧 Open in Spotify</a>',
                    unsafe_allow_html=True
                )
                
                st.write("First few tracks:")
                for i, track in enumerate(tracks[:5]):
                    st.write(f"{i+1}. {track['name']} - {', '.join(a['name'] for a in track['artists'])}")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()