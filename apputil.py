from dotenv import load_dotenv
import os
import requests
import pandas as pd
import difflib
from typing import Optional, List

load_dotenv()


class Genius:
    """Minimal Genius API helper used for the exercises.

    Usage:
        Genius(access_token="<token>")
    or set an environment variable named ACCESS_TOKEN and call:
        Genius()
    """

    def __init__(self, access_token: Optional[str] = None):
        # prefer explicit token, fall back to env var
        self.access_token = access_token or os.environ.get("ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("No access_token provided and ACCESS_TOKEN not found in environment")

        self.base_url = "https://api.genius.com"

    def _request(self, path: str, params: dict = None) -> dict:
        """Make an authorized GET request to the Genius API and return parsed JSON.

        Raises RuntimeError on network/HTTP errors.
        """
        url = self.base_url + path
        headers = {"Authorization": "Bearer " + self.access_token}
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Genius API request failed: {e}")

    def get_artist(self, search_term: str, per_page: int = 5) -> Optional[dict]:
        """Search for `search_term` and return the best-matching artist dict.

        Matching strategy:
        1. Request up to `per_page` search results.
        2. If a primary artist name exactly matches `search_term` (case-insensitive), pick it.
        3. Otherwise, use difflib.get_close_matches to find a close name.
        4. Otherwise fall back to the first hit.

        Returns None when no artist is found.
        """
        params = {"q": search_term, "per_page": per_page}
        data = self._request("/search", params=params)
        hits = data.get("response", {}).get("hits", [])
        if not hits:
            return None

        # Collect candidate primary artists
        candidates = []  # list of tuples (artist_id, artist_name)
        for hit in hits:
            result = hit.get("result", {})
            primary = result.get("primary_artist") or {}
            aid = primary.get("id")
            name = primary.get("name")
            if aid and name:
                candidates.append((aid, name))

        if not candidates:
            return None

        # Normalize search term for comparison
        norm_search = search_term.strip().lower()

        # 1) Exact case-insensitive name match
        for aid, name in candidates:
            if name.strip().lower() == norm_search:
                artist_json = self._request(f"/artists/{aid}")
                return artist_json.get("response", {}).get("artist")

        # 2) Fuzzy match using difflib
        names = [name for (_aid, name) in candidates]
        close = difflib.get_close_matches(search_term, names, n=1, cutoff=0.6)
        if close:
            # find corresponding id
            matched_name = close[0]
            matched_id = next((aid for (aid, name) in candidates if name == matched_name), None)
            if matched_id:
                artist_json = self._request(f"/artists/{matched_id}")
                return artist_json.get("response", {}).get("artist")

        # 3) fall back to first candidate
        fallback_id = candidates[0][0]
        artist_json = self._request(f"/artists/{fallback_id}")
        return artist_json.get("response", {}).get("artist")

    def get_artists(self, search_terms: List[str]) -> pd.DataFrame:
        """Given a list of search terms, return a DataFrame with columns:
        search_term, artist_name, artist_id, followers_count
        """
        rows = []
        for term in search_terms:
            try:
                artist = self.get_artist(term)
            except Exception:
                artist = None

            if artist:
                artist_name = artist.get("name")
                artist_id = artist.get("id")
                # try several places for follower counts
                followers = artist.get("followers_count")
                if followers is None:
                    followers = artist.get("followers")
                if followers is None:
                    followers = artist.get("stats", {}).get("followers")

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
