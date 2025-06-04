from spotify_integration.auth import get_spotify_client
import random
from collections import Counter, defaultdict
import numpy as np
from datetime import datetime, timedelta

MOOD_AUDIO_FEATURES = {
    "happy": {
        "target_valence": 0.8,
        "target_energy": 0.8,
        "target_danceability": 0.7,
        "min_tempo": 120,
        "max_tempo": 140
    },
    "sad": {
        "target_valence": 0.2,
        "target_energy": 0.3,
        "target_danceability": 0.3,
        "min_tempo": 60,
        "max_tempo": 90
    },
    "angry": {
        "target_valence": 0.3,
        "target_energy": 0.9,
        "target_danceability": 0.5,
        "min_tempo": 100,
        "max_tempo": 140
    },
    "calm": {
        "target_valence": 0.5,
        "target_energy": 0.3,
        "target_danceability": 0.3,
        "min_tempo": 70,
        "max_tempo": 100
    }
}

LANGUAGE_CONFIG = {
    'en': {
        'market': 'US',
        'search_terms': ['english', 'american', 'british', 'pop'],
        'seed_artists': [
            "4dpARuHxo51G3z768sgnrY",
            "6eUKZXaKkcviH0Ku9w2n3V",
            "66CXWjxzNUsdJxJ2JdwvnR",
            "06HL4z0CvFAxyc27GXpf02",
            "3TVXtAsR1Inumwj472S9r4"
        ],
        'seed_genres': ['pop', 'rock', 'hip-hop', 'dance', 'indie']
    },
    'es': {
        'market': 'ES',
        'search_terms': ['español', 'latina', 'reggaeton', 'spanish'],
        'seed_artists': [
            "4Z8W4fKeB5YxbusRsdQVPb",
            "790FomKkXshlbRYZFtlgla",
            "7ltDVBr6mKbRvohxheJ9h1",
            "4q3ewBCX7sLwd24euuV69X",
            "4SsVbpTthjScTS7U2hmr1X"
        ],
        'seed_genres': ['latin', 'reggaeton', 'latin-pop', 'spanish']
    },
    'fr': {
        'market': 'FR',
        'search_terms': ['français', 'french', 'chanson'],
        'seed_artists': [
            "5pKCCKE2ajJHZ9KAiaK11H",
            "5a2EaR3hamoenG9rDuVn8j",
            "4xX3cMSRvy9S0OCxq97wEA",
            "3LZZrxsE2OLPfCtr1V7dig",
            "5j4HeCoUlzhfWtjAfM1acR"
        ],
        'seed_genres': ['french', 'chanson', 'variété', 'french-pop']
    },
    'hi': {
        'market': 'IN',
        'search_terms': ['hindi', 'bollywood', 'bhangra'],
        'seed_artists': [
            "7uIbfpbRBj0QSeJcytVOSx",
            "0LyfQWJT6nXafLPZqxe9Of",
            "0oOet2f43PA68X5RxKobEy",
            "5f4QpKfy7ptCHwTqspnSJI",
            "4YRxDV8wJFPHPTeXepOstw"
        ],
        'seed_genres': ['bollywood', 'indian', 'filmi']
    },
    'ko': {
        'market': 'KR',
        'search_terms': ['korean', 'k-pop', '한국어'],
        'seed_artists': [
            "3Nrfpe0tUJi4K4DXYWgMUX",
            "41MozSoPIsD1dJM0CLPjZF",
            "3HqSLMAZ3g3d5poNaI7GOU",
            "1z4g3DjTBBZKhvAroFlhOM",
            "6HvZYsbFfjnjFrWF950C9d"
        ],
        'seed_genres': ['k-pop', 'k-pop-boy-group', 'k-pop-girl-group']
    }
}

def get_comprehensive_user_profile(sp):
    profile = {
        "saved_tracks": {},
        "top_tracks": {},
        "artist_affinity": {},
        "recent_plays": {},
        "genre_preferences": Counter(),
        "preferred_features": {},
        "play_counts": defaultdict(int),
        "skip_rates": {},
        "total_listen_time": 0,
        "listening_time_distribution": {},
        "discovery_rate": 0.3,
        "top_decades": Counter(),
        "popularity_correlation": 0,
    }
    
    try:
        saved_tracks_response = sp.current_user_saved_tracks(limit=50)
        saved_tracks = saved_tracks_response['items']
        
        while saved_tracks_response['next'] and len(saved_tracks) < 200:
            saved_tracks_response = sp.next(saved_tracks_response)
            saved_tracks.extend(saved_tracks_response['items'])
        
        for i, item in enumerate(saved_tracks):
            track = item['track']
            recency_weight = 1.0 - (i / len(saved_tracks)) if len(saved_tracks) > 0 else 1.0
            
            profile["saved_tracks"][track['id']] = {
                'added_at': item['added_at'],
                'recency_weight': recency_weight,
                'name': track['name'],
                'popularity': track['popularity']
            }
            
            for artist in track['artists']:
                profile["artist_affinity"][artist['id']] = profile["artist_affinity"].get(artist['id'], 0) + 3 * recency_weight
        
        time_range_weights = {
            'short_term': 1.0,
            'medium_term': 0.7,
            'long_term': 0.4
        }
        
        for time_range, weight in time_range_weights.items():
            try:
                top_tracks_response = sp.current_user_top_tracks(limit=50, time_range=time_range)
                
                for i, track in enumerate(top_tracks_response['items']):
                    position_score = 1.0 - (i / len(top_tracks_response['items']))
                    score = position_score * weight * 100
                    
                    profile["top_tracks"][track['id']] = max(
                        profile["top_tracks"].get(track['id'], 0), 
                        score
                    )
                    
                    for artist in track['artists']:
                        artist_score = position_score * weight * 5
                        profile["artist_affinity"][artist['id']] = profile["artist_affinity"].get(artist['id'], 0) + artist_score
                        
                        if time_range == 'short_term':
                            estimated_plays = int(20 * (1 - (i/50))) if i < 50 else 1
                            profile["play_counts"][track['id']] += estimated_plays
            except Exception as e:
                print(f"Error getting {time_range} top tracks: {e}")
        
        try:
            recent_tracks = sp.current_user_recently_played(limit=50)
            now = datetime.now()
            
            for item in recent_tracks['items']:
                track = item['track']
                track_id = track['id']
                
                played_at = datetime.strptime(item['played_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
                days_ago = (now - played_at).days + (now - played_at).seconds / 86400
                recency_score = max(0, 1 - (days_ago / 7))
                
                if track_id in profile["recent_plays"]:
                    profile["recent_plays"][track_id]['count'] += 1
                    profile["recent_plays"][track_id]['recency'] = max(
                        profile["recent_plays"][track_id]['recency'], 
                        recency_score
                    )
                else:
                    profile["recent_plays"][track_id] = {
                        'count': 1,
                        'recency': recency_score,
                        'name': track['name']
                    }
                
                profile["play_counts"][track_id] += 1
                
                for artist in track['artists']:
                    profile["artist_affinity"][artist['id']] = profile["artist_affinity"].get(artist['id'], 0) + (1 * recency_score)
                
                hour = played_at.hour
                profile["listening_time_distribution"][hour] = profile["listening_time_distribution"].get(hour, 0) + 1
        except Exception as e:
            print(f"Error getting recently played tracks: {e}")
        
        top_artists_ids = sorted(
            profile["artist_affinity"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:50]
        
        for i in range(0, len(top_artists_ids), 50):
            batch = [artist_id for artist_id, _ in top_artists_ids[i:i+50]]
            if not batch:
                continue
                
            try:
                artists_data = sp.artists(batch)['artists']
                
                for artist in artists_data:
                    artist_id = artist['id']
                    if artist_id not in profile["artist_affinity"]:
                        continue
                        
                    weight = profile["artist_affinity"][artist_id]
                    
                    for genre in artist['genres']:
                        profile["genre_preferences"][genre] += weight
                    
                    profile["popularity_correlation"] += (artist['popularity'] / 100) * weight
            except Exception as e:
                print(f"Error processing artist batch: {e}")
        
        if top_artists_ids:
            total_weight = sum(weight for _, weight in top_artists_ids)
            if total_weight > 0:
                profile["popularity_correlation"] /= total_weight
        
        track_ids = list(set(list(profile["saved_tracks"].keys()) + list(profile["top_tracks"].keys())))
        if track_ids:
            all_features = []
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i+100]
                try:
                    features = sp.audio_features(batch)
                    all_features.extend([f for f in features if f])
                except Exception as e:
                    print(f"Error getting audio features: {e}")
            
            if all_features:
                feature_keys = [
                    'danceability', 'energy', 'valence', 'acousticness', 
                    'instrumentalness', 'tempo', 'loudness', 'speechiness'
                ]
                
                for key in feature_keys:
                    values = [f[key] for f in all_features if key in f]
                    if values:
                        avg = sum(values) / len(values)
                        std = np.std(values) if len(values) > 1 else 0.15
                        
                        profile["preferred_features"][key] = {
                            'mean': avg,
                            'std': std,
                            'min': max(0, avg - std),
                            'max': min(1, avg + std)
                        }
        
        try:
            short_term = set(track['id'] for track in sp.current_user_top_tracks(limit=50, time_range='short_term')['items'])
            long_term = set(track['id'] for track in sp.current_user_top_tracks(limit=50, time_range='long_term')['items'])
            
            if short_term and long_term:
                new_tracks = short_term - long_term
                discovery_rate = len(new_tracks) / len(short_term) if short_term else 0.3
                profile["discovery_rate"] = discovery_rate
        except:
            profile["discovery_rate"] = 0.3
        
        return profile
        
    except Exception as e:
        print(f"Error building user profile: {e}")
        return profile

def calculate_preference_score(track, user_profile):
    score = 50
    track_id = track['id']
    
    if track_id in user_profile["saved_tracks"]:
        saved_info = user_profile["saved_tracks"][track_id]
        score += 30 * saved_info['recency_weight']
    
    if track_id in user_profile["top_tracks"]:
        score += user_profile["top_tracks"][track_id] * 0.3
    
    if track_id in user_profile["recent_plays"]:
        recent_info = user_profile["recent_plays"][track_id]
        recency_boost = 15 * recent_info['recency']
        count_boost = min(recent_info['count'] * 2, 10)
        score += recency_boost + count_boost
    
    if track_id in user_profile["play_counts"]:
        play_count = user_profile["play_counts"][track_id]
        score += min(play_count * 1, 15)
    
    artist_score = 0
    for artist in track['artists']:
        if artist['id'] in user_profile["artist_affinity"]:
            artist_score = max(artist_score, user_profile["artist_affinity"][artist['id']])
    
    if artist_score > 0:
        max_affinity = max(user_profile["artist_affinity"].values()) if user_profile["artist_affinity"] else 1
        scaled_artist_score = (artist_score / max_affinity) * 25
        score += scaled_artist_score
    
    if user_profile["genre_preferences"]:
        track_genres = []
        for artist in track['artists']:
            if artist['id'] in user_profile["artist_affinity"]:
                try:
                    artist_full = sp.artist(artist['id'])
                    track_genres.extend(artist_full['genres'])
                except:
                    pass
        
        if track_genres:
            genre_score = 0
            for genre in track_genres:
                genre_score += user_profile["genre_preferences"][genre]
            
            max_genre_score = sum(user_profile["genre_preferences"].most_common(1)[0][1]) if user_profile["genre_preferences"] else 1
            if max_genre_score > 0:
                scaled_genre_score = (genre_score / max_genre_score) * 15
                score += scaled_genre_score
    
    return min(score, 100)

def calculate_mood_match_score(track, mood_features, audio_features):
    if not audio_features:
        return 50
    
    score = 50
    
    targets = {k: v for k, v in mood_features.items() 
               if not k.startswith('min_') and not k.startswith('max_')}
    
    matches = []
    for feature, target in targets.items():
        if feature in audio_features:
            diff = abs(audio_features[feature] - target)
            match_pct = max(0, 1 - (diff * 2))
            matches.append(match_pct)
    
    if matches:
        avg_match = sum(matches) / len(matches)
        score = 50 + (avg_match * 50)
    
    if mood_features == MOOD_AUDIO_FEATURES['happy']:
        if audio_features['valence'] > 0.7 and audio_features['energy'] > 0.65:
            score += 15
    elif mood_features == MOOD_AUDIO_FEATURES['sad']:
        if audio_features['valence'] < 0.3 and audio_features['energy'] < 0.4:
            score += 15
    elif mood_features == MOOD_AUDIO_FEATURES['angry']:
        if audio_features['energy'] > 0.8 and audio_features['valence'] < 0.4:
            score += 15
    elif mood_features == MOOD_AUDIO_FEATURES['calm']:
        if audio_features['energy'] < 0.4 and audio_features['acousticness'] > 0.6:
            score += 15
            
    return min(score, 100)

def calculate_trend_score(track, user_profile):
    score = 50
    
    popularity = track['popularity']
    
    pop_correlation = user_profile.get("popularity_correlation", 0.5)
    
    adjusted_popularity = popularity * pop_correlation
    
    score = 50 + (adjusted_popularity / 2)
    
    try:
        album = track['album']
        if 'release_date' in album:
            release_date = album['release_date']
            release_year = int(release_date.split('-')[0])
            current_year = datetime.now().year
            
            if release_year >= current_year - 1:
                score += 20
            elif release_year >= current_year - 2:
                score += 10
    except:
        pass
    
    return min(score, 100)

def create_personalized_playlist(mood, language_code, limit, user_profile=None):
    sp = get_spotify_client()
    
    try:
        current_user = sp.current_user()
        print(f"Connected as: {current_user['display_name']}")
    except Exception as e:
        print(f"Authentication error: {e}")
    
    if not user_profile:
        user_profile = get_comprehensive_user_profile(sp)
    
    mood_features = MOOD_AUDIO_FEATURES.get(mood.lower(), MOOD_AUDIO_FEATURES["happy"])
    lang_config = LANGUAGE_CONFIG.get(language_code, LANGUAGE_CONFIG['en'])
    
    candidate_tracks = []
    
    seed_tracks = []
    
    if user_profile["saved_tracks"] or user_profile["top_tracks"]:
        all_user_tracks = set(user_profile["saved_tracks"].keys()) | set(user_profile["top_tracks"].keys())
        
        if all_user_tracks:
            track_features = {}
            for i in range(0, len(all_user_tracks), 100):
                batch = list(all_user_tracks)[i:i+100]
                try:
                    features = sp.audio_features(batch)
                    for feature in features:
                        if feature:
                            track_features[feature['id']] = feature
                except Exception as e:
                    print(f"Error getting audio features: {e}")
            
            mood_matches = []
            for track_id, features in track_features.items():
                if mood == "happy":
                    if features['valence'] > 0.6 and features['energy'] > 0.6:
                        mood_matches.append(track_id)
                elif mood == "sad":
                    if features['valence'] < 0.4 and features['energy'] < 0.5:
                        mood_matches.append(track_id)
                elif mood == "angry":
                    if features['energy'] > 0.7 and features['valence'] < 0.5:
                        mood_matches.append(track_id)
                elif mood == "calm":
                    if features['energy'] < 0.5 and features['acousticness'] > 0.4:
                        mood_matches.append(track_id)
            
            if mood_matches:
                seed_tracks = mood_matches[:5]
    
    seed_artists = []
    if user_profile["artist_affinity"]:
        top_artists = sorted(
            user_profile["artist_affinity"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        seed_artists = [artist_id for artist_id, _ in top_artists[:2]]
    
    success = False
    if seed_tracks or seed_artists:
        try:
            recs = sp.recommendations(
                seed_tracks=seed_tracks[:5] if seed_tracks else None,
                seed_artists=seed_artists[:2] if seed_artists else None,
                limit=limit * 2,
                market=lang_config['market'],
                **{k: v for k, v in mood_features.items() if not k.startswith('min_') and not k.startswith('max_')}
            )
            
            if recs and 'tracks' in recs and recs['tracks']:
                candidate_tracks.extend(recs['tracks'])
                success = True
            else:
                print("Warning: No tracks returned from personal recommendations")
        except Exception as e:
            print(f"Error getting personalized recommendations: {e}")
    
    FALLBACK_GENRE_SEEDS = [
        'acoustic', 'afrobeat', 'alt-rock', 'alternative', 'ambient', 'blues',
        'classical', 'country', 'dance', 'electronic', 'folk', 'hip-hop', 'house',
        'indie', 'jazz', 'k-pop', 'latin', 'metal', 'pop', 'r-b', 'reggae',
        'reggaeton', 'rock', 'soul'
    ]
    
    top_genres = []
    if user_profile["genre_preferences"]:
        try:
            available_genres = sp.recommendation_genre_seeds()['genres']
        except Exception as e:
            print(f"Error getting genre seeds: {e} - using fallback genres")
            available_genres = FALLBACK_GENRE_SEEDS
            
        for genre, _ in user_profile["genre_preferences"].most_common(5):
            for available in available_genres:
                if genre == available or genre in available or available in genre:
                    top_genres.append(available)
                    break
    
    if top_genres:
        try:
            recs = sp.recommendations(
                seed_genres=top_genres[:5],
                limit=limit,
                market=lang_config['market'],
                **{k: v for k, v in mood_features.items() if not k.startswith('min_') and not k.startswith('max_')}
            )
            
            if recs and 'tracks' in recs and recs['tracks']:
                candidate_tracks.extend(recs['tracks'])
                success = True
            else:
                print("Warning: No tracks returned from genre recommendations")
        except Exception as e:
            print(f"Error getting genre recommendations: {e}")
    
    if not success or len(candidate_tracks) < limit:
        try:
            if not lang_config['seed_artists']:
                print("Warning: No seed artists for this language. Using default artists.")
                lang_config['seed_artists'] = [
                    "4Z8W4fKeB5YxbusRsdQVPb",
                    "06HL4z0CvFAxyc27GXpf02",
                    "3TVXtAsR1Inumwj472S9r4"
                ]
            
            if not lang_config['seed_genres']:
                print("Warning: No seed genres for this language. Using default genres.")
                lang_config['seed_genres'] = ['pop', 'rock']
            
            selected_artists = random.sample(
                lang_config['seed_artists'], 
                min(2, len(lang_config['seed_artists']))
            )
            
            selected_genre = random.sample(
                lang_config['seed_genres'], 
                min(1, len(lang_config['seed_genres']))
            )
            
            recs = sp.recommendations(
                seed_artists=selected_artists,
                seed_genres=selected_genre,
                limit=limit * 2,
                market=lang_config['market'],
                **{k: v for k, v in mood_features.items() if not k.startswith('min_') and not k.startswith('max_')}
            )
            
            if recs and 'tracks' in recs and recs['tracks']:
                candidate_tracks.extend(recs['tracks'])
                success = True
            else:
                print("Warning: No tracks returned from language recommendations")
        except Exception as e:
            print(f"Error getting language recommendations: {e}")
    
    if not candidate_tracks:
        print("All recommendation strategies failed. Using search as last resort.")
        try:
            search_terms = [mood]
            if language_code in LANGUAGE_CONFIG:
                search_terms.extend(LANGUAGE_CONFIG[language_code]['search_terms'])
            
            query = " ".join(search_terms)
            search_results = sp.search(
                q=query,
                type='track',
                limit=limit,
                market=lang_config['market']
            )
            
            if search_results and 'tracks' in search_results and search_results['tracks']['items']:
                candidate_tracks.extend(search_results['tracks']['items'])
            else:
                print("ERROR: Even search fallback returned no tracks")
                return []
        except Exception as e:
            print(f"Error in fallback search: {e}")
            return []
    
    scored_tracks = []
    track_ids = []
    
    unique_tracks = []
    seen_ids = set()
    for track in candidate_tracks:
        if track['id'] not in seen_ids:
            unique_tracks.append(track)
            seen_ids.add(track['id'])
            track_ids.append(track['id'])
    
    audio_features = {}
    if track_ids:
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            try:
                features = sp.audio_features(batch)
                for feature in features:
                    if feature:
                        audio_features[feature['id']] = feature
            except Exception as e:
                print(f"Error getting audio features for scoring: {e}")
    
    for track in unique_tracks:
        track_id = track['id']
        features = audio_features.get(track_id, None)
        
        preference_score = calculate_preference_score(track, user_profile)
        mood_match_score = calculate_mood_match_score(track, mood_features, features) if features else 50
        trend_score = calculate_trend_score(track, user_profile)
        
        total_score = (0.5 * preference_score) + (0.3 * mood_match_score) + (0.2 * trend_score)
        
        scored_tracks.append({
            'track': track,
            'score': total_score,
            'components': {
                'preference': preference_score,
                'mood_match': mood_match_score,
                'trend': trend_score
            }
        })
    
    scored_tracks.sort(key=lambda x: x['score'], reverse=True)
    
    final_playlist = []
    artist_counts = {}
    included_ids = set()
    
    discovery_rate = user_profile.get("discovery_rate", 0.3)
    exploration_count = int(limit * discovery_rate)
    
    known_artists = set(user_profile["artist_affinity"].keys())
    
    known_tracks = []
    exploration_tracks = []
    
    for item in scored_tracks:
        track = item['track']
        
        is_known = any(artist['id'] in known_artists for artist in track['artists'])
        
        if is_known:
            known_tracks.append(item)
        else:
            exploration_tracks.append(item)
    
    for item in known_tracks:
        track = item['track']
        
        if track['id'] in included_ids:
            continue
        
        primary_artist = track['artists'][0]['id']
        if artist_counts.get(primary_artist, 0) >= 2:
            continue
        
        final_playlist.append(track)
        included_ids.add(track['id'])
        
        artist_counts[primary_artist] = artist_counts.get(primary_artist, 0) + 1
        
        if len(final_playlist) >= (limit - exploration_count):
            break
    
    for item in exploration_tracks:
        if len(final_playlist) >= limit:
            break
            
        track = item['track']
        
        if track['id'] in included_ids:
            continue
        
        primary_artist = track['artists'][0]['id']
        if artist_counts.get(primary_artist, 0) >= 1:
            continue
        
        final_playlist.append(track)
        included_ids.add(track['id'])
        
        artist_counts[primary_artist] = artist_counts.get(primary_artist, 0) + 1
    
    if len(final_playlist) < limit:
        for item in scored_tracks:
            if len(final_playlist) >= limit:
                break
                
            track = item['track']
            
            if track['id'] in included_ids:
                continue
            
            final_playlist.append(track)
            included_ids.add(track['id'])
    
    print(f"Successfully created playlist with {len(final_playlist)} tracks")
    return final_playlist[:limit]

def get_tracks_by_mood(mood: str, language_code: str = 'en', limit: int = 20):
    sp = get_spotify_client()
    user_profile = get_comprehensive_user_profile(sp)
    return create_personalized_playlist(mood, language_code, limit, user_profile)