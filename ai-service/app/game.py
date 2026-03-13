import requests

RAWG_API_KEY = "e6fe4d3cc42341bd9ca37e7ad8c5911f"

def search_game(game_name):

    url = "https://api.rawg.io/api/games"

    params = {
        "key": RAWG_API_KEY,
        "search": game_name
    }

    response = requests.get(url, params=params)

    return response.json()