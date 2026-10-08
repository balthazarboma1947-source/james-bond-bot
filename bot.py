import os
import requests
from bs4 import BeautifulSoup

print("JAMES BOND BOT TEST GESTART")

url = "https://www.2dehands.be/q/zoeken/?query=James%20Bond"

headers = {
"User-Agent": "Mozilla/5.0"
}

response = requests.get(
url,
headers=headers,
timeout=30
)

print("HTTP status:", response.status_code)

soup = BeautifulSoup(
response.text,
"html.parser"
)

links = []

for link in soup.find_all("a", href=True):

href = link["href"]
titel = link.get_text(" ", strip=True)

if "/v/" not in href:
    continue

if not titel:
    continue

if href.startswith("/"):
    href = "https://www.2dehands.be" + href

if href not in [item["link"] for item in links]:

    links.append({
        "titel": titel,
        "link": href
    })

if len(links) >= 10:
    break

print("Aantal gevonden:", len(links))

for item in links:

print("TITEL:", item["titel"])
print("LINK:", item["link"])
print("---")

print("TEST KLAAR")
