from flask import Flask, jsonify, request
from ytmusicapi import YTMusic
from pytube import YouTube
import json
import requests
import re

import yt_dlp

app = Flask(__name__)
yt = YTMusic()


@app.route('/trending', methods=['GET'])
def get_new_trending():
    """Get trending new songs in India with robust artist handling"""
    try:
        charts = yt.get_charts(country="IN")
        
        if 'videos' not in charts or 'items' not in charts['videos']:
            return jsonify({
                "error": "No trending data available",
                "solution": "Try again later or check API updates"
            }), 404
        
        new_songs = []
        for item in charts['videos']['items'][:20]:
            if not item.get('videoId'):
                continue
                
            # Improved artist handling
            artists = []
            for artist in item.get('artists', []):
                if isinstance(artist, dict):
                    name = artist.get('name')
                    if name and not any(x in name.lower() for x in ['min', 'sec', 'hour']):  # Skip duration strings
                        artists.append(name)
                elif isinstance(artist, str):
                    if not any(x in artist.lower() for x in ['min', 'sec', 'hour']):
                        artists.append(artist)
            
            # Fallback for missing artists
            if not artists:
                artists = ["Artist info unavailable"]
            
            # Get duration (fallback to empty string)
            duration = item.get('duration', '0:00')
            if any(x in duration.lower() for x in ['min', 'sec']):  # Sometimes duration appears in artist field
                duration = '0:00'
                
            new_songs.append({
                "title": item.get('title', 'Unknown Title'),
                "artists": artists,
                "videoId": item['videoId'],
                "views": item.get('views', 'N/A'),
                "duration": duration,
                "thumbnail": item.get('thumbnails', [{}])[0].get('url', '')
            })
        
        return jsonify({
            "country": "India",
            "count": len(new_songs),
            "songs": new_songs
        })
        
    except Exception as e:
        return jsonify({
            "error": "Failed to fetch trending songs",
            "details": str(e)
        }), 500

# Endpoint 2: Search Songs
@app.route('/search', methods=['GET'])
def search_songs():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Missing search query"}), 400
    
    results = yt.search(query, filter="songs")
    return jsonify({
        "results": [{
            "title": song['title'],
            "artists": [a['name'] for a in song['artists']],
            "videoId": song['videoId'],
            "duration": song['duration']
        } for song in results[:10]]  # Top 10 results
    })


@app.route('/play', methods=['GET'])
def play_song():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "Missing video ID"}), 400

    # Method 1: Try yt-dlp first (most reliable)
    try:
        with yt_dlp.YoutubeDL({
            'format': 'bestaudio/best',
            'quiet': True,
            'extract_flat': True,
            'forceurl': True,
        }) as ydl:
            info = ydl.extract_info(f'https://youtube.com/watch?v={video_id}', download=False)
            return jsonify({
                "stream_url": info['url'],
                "title": info.get('title', ''),
                "duration": info.get('duration', 0),
                "thumbnail": info.get('thumbnail', ''),
                "method": "yt-dlp"
            })
    except Exception as e:
        print(f"yt-dlp failed: {str(e)}")

    # Method 2: Fallback to player API extraction
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        # First get the base video page
        response = requests.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers=headers
        )
        response.raise_for_status()
        
        # Extract player config
        match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;', response.text)
        if not match:
            raise ValueError("Couldn't extract player response")
            
        player_response = json.loads(match.group(1))
        
        # Get streaming data
        streaming_data = player_response.get('streamingData', {})
        formats = streaming_data.get('formats', []) + streaming_data.get('adaptiveFormats', [])
        
        # Find best audio stream
        audio_streams = [
            f for f in formats 
            if f.get('mimeType', '').startswith('audio/') 
            and f.get('url')
        ]
        
        if not audio_streams:
            raise ValueError("No audio streams found")
            
        best_stream = max(audio_streams, key=lambda x: int(x.get('bitrate', 0)))
        
        return jsonify({
            "stream_url": best_stream['url'],
            "title": player_response.get('videoDetails', {}).get('title', ''),
            "duration": player_response.get('videoDetails', {}).get('lengthSeconds', 0),
            "thumbnail": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
            "method": "player_api"
        })
        
    except Exception as e:
        print(f"Player API failed: {str(e)}")

    # Method 3: Final fallback to Invidious API
    try:
        invidious_instances = [
            "https://vid.puffyan.us",
            "https://invidious.snopyta.org",
            "https://yt.artemislena.eu"
        ]
        
        for instance in invidious_instances:
            try:
                response = requests.get(f"{instance}/api/v1/videos/{video_id}", timeout=5)
                data = response.json()
                if 'formatStreams' in data and data['formatStreams']:
                    return jsonify({
                        "stream_url": data['formatStreams'][0]['url'],
                        "title": data.get('title', ''),
                        "duration": data.get('lengthSeconds', 0),
                        "thumbnail": data.get('videoThumbnails', [{}])[-1].get('url', ''),
                        "method": "invidious"
                    })
            except:
                continue
                
        raise ValueError("All Invidious instances failed")
        
    except Exception as e:
        print(f"Invidious failed: {str(e)}")

    return jsonify({
        "error": "All methods failed to fetch stream",
        "solution": "YouTube's API may have changed. Try again later or use official YouTube API."
    }), 503
    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
