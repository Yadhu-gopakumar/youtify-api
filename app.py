from flask import Flask, jsonify, request
from flask_cors import CORS
from ytmusicapi import YTMusic
import subprocess

app = Flask(__name__)
CORS(app)  


@app.route('/')
def home():
    return jsonify({"message": "Youtify music app api-yadhu"})


def get_audio_url(video_id):
    try:
        cmd = [
            'yt-dlp',
            '-f', 'bestaudio',
            '--get-url',
            f'https://www.youtube.com/watch?v={video_id}'
        ]
        result = subprocess.check_output(cmd, timeout=10).decode('utf-8').strip()
        return result
    except Exception as e:
        print(f"Error fetching audio URL for {video_id}: {e}")
        return None



# Fetch popular or trending songs
@app.route('/trending', methods=['GET'])
def trending():
    ytmusic = YTMusic()
    region = request.args.get('region', 'IN')  # Default to 'IN' (India)

    try:
        # Search for popular songs or playlists (Example search for 'trending')
        search_results = ytmusic.search('trending', limit=10)
        audio_url = get_audio_url(song['videoId'])
        # Format the response to return only the song title and videoId
        trending_results = [{
            'title': song['title'],
            'videoId': song['videoId'],
            'artists': [artist['name'] for artist in song['artists']],
            'audioUrl': audio_url
        } for song in search_results if 'videoId' in song]

        return jsonify(trending_results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Search for songs, artists, albums, etc.
@app.route('/search', methods=['GET'])
def search():
    ytmusic = YTMusic()
    query = request.args.get('query', '')  # Get the search query from the request
    limit = int(request.args.get('limit', 10))  # Default limit of 10 results

    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    try:
        # Perform the search based on the query
        search_results = ytmusic.search(query, limit=limit)
        audio_url = get_audio_url(song['videoId'])
        # Format the response to return only relevant details like title, videoId, and artists
        search_results_formatted = [{
            'title': song['title'],
            'videoId': song['videoId'],
            'artists': [artist['name'] for artist in song['artists']],
            'audioUrl': audio_url
        } for song in search_results if 'videoId' in song]

        return jsonify(search_results_formatted)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
