from dotenv import load_dotenv
import os
import requests
import pandas as pd
from typing import List

load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

class Genius:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.genius.com"

    def get(self, path: str, params: dict = None) -> dict:
        url = self.base_url + path
        headers = {"Authorization": "Bearer " + self.access_token}
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Genius API request failed: {e}")

    def get_artist(self, search_term: str) -> dict:
        headers = {"Authorization": "Bearer " + self.access_token}
        search_url = f"{self.base_url}/search"
        search_response = requests.get(search_url, headers=headers, params={"q": search_term})
        search_data = search_response.json()

        hits = search_data.get("response", {}).get("hits", [])
        if not hits:
            print(f"No hits for {search_term}")
            return None
        first_hit = hits[0]
        artist_id = first_hit["result"]["primary_artist"]["id"]

        artist_url = f"{self.base_url}/artists/{artist_id}"
        artist_response = requests.get(artist_url, headers=headers)
        artist_data = artist_response.json()
        return artist_data

    def get_artists(self, search_terms: List[str]) -> pd.DataFrame:
        rows = []
        for term in search_terms:
            try:
                artist_json = self.get_artist(term)
            except Exception as e:
                print(f"Error for {term}: {e}")
                artist_json = None

            if artist_json:
                # since get_artist returns full JSON, dig into response
                artist_data = artist_json.get("response", {}).get("artist", {})
                artist_name = artist_data.get("name")
                artist_id = artist_data.get("id")
                followers = artist_data.get("followers_count") or \
                            artist_data.get("followers") or \
                            artist_data.get("stats", {}).get("followers")
            else:
                artist_name = None
                artist_id = None
                followers = None

            rows.append({
                "search_term": term,
                "artist_name": artist_name,
                "artist_id": artist_id,
                "followers_count": followers,
        })

        df = pd.DataFrame(rows, columns=["search_term", "artist_name", "artist_id", "followers_count"])
    return df


if __name__ == "__main__":
    genius = Genius(ACCESS_TOKEN)
    terms = ["Rihanna", "BBno$", "Fall Out Boy", "Panic at the Disco", "Mitzki"]
    df = genius.get_artists(terms)
    print(df)
