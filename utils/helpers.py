from typing import List, Dict, Any

def format_track_display(tracks: List[Dict[str, Any]]) -> str:
    """
    Format track list for display
    
    Args:
        tracks: List of track objects
    
    Returns:
        Formatted string of track names and artists
    """
    return "\n".join(
        f"{i+1}. {track['name']} - {', '.join(a['name'] for a in track['artists'])}"
        for i, track in enumerate(tracks)
    )

def validate_mood(mood: str) -> str:
    """
    Validate and standardize mood labels
    
    Args:
        mood: Raw mood label
    
    Returns:
        Standardized mood label
    """
    mood = mood.lower()
    valid_moods = ["happy", "sad", "angry", "calm", "neutral"]
    
    mood_mapping = {
        "joyful": "happy",
        "excited": "happy",
        "depressed": "sad",
        "melancholy": "sad",
        "furious": "angry",
        "peaceful": "calm",
        "relaxed": "calm"
    }
    
    if mood in valid_moods:
        return mood
    return mood_mapping.get(mood, "neutral")