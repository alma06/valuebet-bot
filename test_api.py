import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")
url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={api_key}&regions=us&markets=h2h"

print(f"Testing API with key: {api_key[:10]}...")
print(f"URL: {url[:80]}...")
print()

r = requests.get(url)
print(f"Status Code: {r.status_code}")
print(f"Response: {r.text[:300]}")

if r.status_code == 401:
    print("\n❌ API Key inválida o vencida")
    print("👉 Verifica en: https://the-odds-api.com/account/")
elif r.status_code == 429:
    print("\n⚠️  Sin créditos disponibles")
    print("👉 Compra más requests en: https://the-odds-api.com/account/")
elif r.status_code == 404:
    print("\n⚠️  Deporte no disponible ahora")
