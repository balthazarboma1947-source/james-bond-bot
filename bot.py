import requests
from bs4 import BeautifulSoup

print("JAMES BOND BOT TEST GESTART")

url = "https://www.2dehands.be/q/zoeken/?query=James%20Bond"

response = requests.get(
url,
headers={"User-Agent": "Mozilla/5.0"},
timeout=30
)

print("HTTP status:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

print("Pagina geladen:", soup.title.get_text(strip=True) if soup.title else "geen titel")

print("TEST KLAAR")
