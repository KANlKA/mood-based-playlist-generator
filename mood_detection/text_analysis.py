from transformers import pipeline
import numpy as np

mood_analyzer = pipeline("text-classification", 
                        model="finiteautomata/bertweet-base-sentiment-analysis")

MOOD_MAPPING = {
    'joy': 'happy',
    'happy': 'happy',
    'excited': 'energetic',
    'energetic': 'energetic',
    'sad': 'sad',
    'sadness': 'sad',
    'depressed': 'sad',
    'angry': 'angry',
    'furious': 'angry',
    'calm': 'calm',
    'peaceful': 'calm',
    'romantic': 'romantic',
    'love': 'romantic',
    'focus': 'focus',
    'workout': 'workout',
    'party': 'party'
}

def detect_mood_from_text(text):
    try:
        result = mood_analyzer(text[:512])[0]
        primary_mood = result['label'].lower()
        confidence = result['score']
        
        detected_mood = MOOD_MAPPING.get(primary_mood, 'neutral')
        
        return detected_mood, float(confidence)
    except:
        return 'neutral', 0.5