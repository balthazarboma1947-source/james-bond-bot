import requests
from bs4 import BeautifulSoup

print("JAMES BOND BOT GESTART")

url = "https://www.2dehands.be/q/zoeken/?query=James%20Bond"

response = requests.get(
url,
headers={"User-Agent": "Mozilla/5.0"},
timeout=30
)

print("HTTP status:", response.status_code)

soup = BeautifulSoup(
response.text,
"html.parser"
)

advertenties = soup.select("a[href*='/v/']")

print(
"Aantal mogelijke advertenties:",
len(advertenties)
)

teller = 0

for advertentie in advertenties:

```
titel = advertentie.get_text(
    " ",
    strip=True
)

link = advertentie.get("href")

if not titel:
    continue

if not link:
    continue

if link.startswith("/"):
    link = "https://www.2dehands.be" + link

print("")
print("TITEL:", titel)
print("LINK:", link)

teller = teller + 1

if teller >= 10:
    break
```

print("")
print("TEST KLAAR")
