import asyncio
import aiohttp

async def test():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"
    params = {
        "apiKey": "150207186f18e9b71b62a8c464c2a959",
        "regions": "us",
        "markets": "h2h"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            print(f"Status: {resp.status}")
            text = await resp.text()
            print(f"Response: {text[:200]}")

asyncio.run(test())
