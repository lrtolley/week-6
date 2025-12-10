from dotenv import load_dotenv
import os
import requests
import pandas as pd
import difflib
from typing import Optional, List

load_dotenv()

genius_search_url = f"http://api.genius.com/search?q={search_term}"

response = requests.get(genius_search_url, 
                        headers={"Authorization": "Bearer " + ACCESS_TOKEN})
json_data = response.json()

class Genius:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.genius.com"


 def get(self, path: str, params: dict = None) -> dict:
        """Make an authorized GET request to the Genius API and return parsed JSON.
        """
        url = self.base_url + path
        headers = {"Authorization": "Bearer " + self.access_token}
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Genius API request failed: {e}")

    def get_artist(self, search_term: str) -> dict:
        headers = {"Authorization": "Bearer " + self.access_token}
      
        search_url = f"{self.base_url}/search"
        search_response = requests.get(search_url, headers=headers, params={"q": search_term})
        search_data = search_response.json()
        
        first_hit = search_data["response"]["hits"][0]
        
        artist_id = first_hit["result"]["primary_artist"]["id"]
        artist_url = f"{self.base_url}/artists/{artist_id}"
        artist_response = requests.get(artist_url, headers=headers)
        artist_data = artist_response.json()
        return artist_data["response"]["artist"]
  
    def get_artists(self, search_terms: List[str]) -> pd.DataFrame:
        rows = []
    for term in search_terms:
        try:
            artist_json = self.get_artist(term)
        except Exception:
            artist_json = None

        if artist_json:
            artist_data = artist_json.get("response", {}).get("artist", {})
            artist_name = artist_data.get("name")
            artist_id = artist_data.get("id")
            followers = artist_data.get("followers_count") or \
                        artist_data.get("followers") or \
                        artist_data.get("stats", {}).get("followers")

            rows.append({
                "search_term": term,
                "artist_name": artist_name,
                "artist_id": artist_id,
                "followers_count": followers,
            })
        else:
            rows.append({
                "search_term": term,
                "artist_name": None,
                "artist_id": None,
                "followers_count": None,
            })

    df = pd.DataFrame(rows, columns=["search_term", "artist_name", "artist_id", "followers_count"])
    return df

if __name__ == "__main__":
    # small smoke test. Requires ACCESS_TOKEN in env or pass token explicitly.
    try:
        genius = Genius()
    except ValueError as e:
        print("Skipping live smoke test: ", e)
    else:
        terms = ["Rihanna", "Seal", "U2", "Fall Out Boy"]
        df = genius.get_artists(terms)
        print(df)
