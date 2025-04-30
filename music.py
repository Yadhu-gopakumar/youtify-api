from flask import Flask, jsonify, request
from ytmusicapi import YTMusic

app = Flask(__name__)
ytmusic = YTMusic()

# Fetch popular or trending songs
@app.route('/trending', methods=['GET'])
def trending():
    region = request.args.get('region', 'IN')  # Default to 'IN' (India)

    try:
        # Search for popular songs or playlists (Example search for 'trending')
        search_results = ytmusic.search('trending', limit=10)

        # Format the response to return only the song title and videoId
        trending_results = [{
            'title': song['title'],
            'videoId': song['videoId'],
            'artists': [artist['name'] for artist in song['artists']]
        } for song in search_results if 'videoId' in song]

        return jsonify(trending_results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Search for songs, artists, albums, etc.
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')  # Get the search query from the request
    limit = int(request.args.get('limit', 10))  # Default limit of 10 results

    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    try:
        # Perform the search based on the query
        search_results = ytmusic.search(query, limit=limit)

        # Format the response to return only relevant details like title, videoId, and artists
        search_results_formatted = [{
            'title': song['title'],
            'videoId': song['videoId'],
            'artists': [artist['name'] for artist in song['artists']]
        } for song in search_results if 'videoId' in song]

        return jsonify(search_results_formatted)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
