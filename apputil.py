from dotenv import load_dotenv
import os

ACCESS_TOKEN = os.environ['wkKOf5ZVIQKtx5QRpgUoRHo9iUTaMxh4ghmZsUS-KyP-gij_5WYKZXrhTa3_RvFS']

load_dotenv()

search_term = "Missy Elliott"
genius_search_url = f"http://api.genius.com/search?q={search_term}&access_token={ACCESS_TOKEN}"