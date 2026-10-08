```python
import json
import os
import re
import smtplib
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


# ============================================================
# INSTELLINGEN
# ============================================================

ZOEKOPDRACHTEN = [
    "James Bond",
    "007",
    "James Bond memorabilia",
    "James Bond collectible",
    "James Bond collection",
]

MAX_RESULTATEN = 25

SEEN_FILE = Path("seen.json")
EERSTE_RUN_FILE = Path("first_run_done.txt")


# ============================================================
# E-MAIL INSTELLINGEN
# ============================================================

EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "465"))

EMAIL_USERNAME = os.environ["EMAIL_USERNAME"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]

EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_TO = os.environ["EMAIL_TO"]


# ============================================================
# E-MAIL VERSTUREN
# ============================================================

def stuur_email(titel, zoekterm, prijs, link, beschrijving=""):

    bericht = EmailMessage()

    bericht["Subject"] = f"Nieuwe James Bond-match: {titel}"
    bericht["From"] = EMAIL_FROM
    bericht["To"] = EMAIL_TO

    tekst = "🕵️ NIEUWE JAMES BOND-ADVERTENTIE\n\n"

    tekst += f"Zoekterm: {zoekterm}\n"
    tekst += f"Titel: {titel}\n"

    if prijs is not None:
        tekst += f"Prijs: €{prijs:g}\n"

    if beschrijving:

        beschrijving_schoon = re.sub(
            r"<[^>]+>",
            " ",
            beschrijving,
        )

        beschrijving_schoon = re.sub(
            r"\s+",
            " ",
            beschrijving_schoon,
        ).strip()

        if len(beschrijving_schoon) > 500:
            beschrijving_schoon = (
                beschrijving_schoon[:500] + "..."
            )

        tekst += f"\nBeschrijving:\n{beschrijving_schoon}\n"

    tekst += f"\nBekijk de advertentie:\n{link}\n"

    bericht.set_content(tekst)

    with smtplib.SMTP_SSL(
        EMAIL_HOST,
        EMAIL_PORT,
        timeout=30,
    ) as smtp:

        smtp.login(
            EMAIL_USERNAME,
            EMAIL_PASSWORD,
        )

        smtp.send_message(bericht)

    print(f"E-mail verstuurd: {titel}")


# ============================================================
# GEZIEN ADVERTENTIES
# ============================================================

def laad_gezien():

    if not SEEN_FILE.exists():
        return set()

    try:

        with open(
            SEEN_FILE,
            "r",
            encoding="utf-8",
        ) as bestand:

            return set(json.load(bestand))

    except Exception:

        return set()


def bewaar_gezien(gezien):

    with open(
        SEEN_FILE,
        "w",
        encoding="utf-8",
    ) as bestand:

        json.dump(
            sorted(gezien),
            bestand,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# PRIJS HERKENNEN
# ============================================================

def vind_prijs(tekst):

    patronen = [
        r"€\s*([0-9][0-9\.,]*)",
        r"EUR\s*([0-9][0-9\.,]*)",
        r"([0-9][0-9\.,]*)\s*€",
        r"([0-9][0-9\.,]*)\s*EUR",
    ]

    for patroon in patronen:

        match = re.search(
            patroon,
            tekst,
            re.IGNORECASE,
        )

        if not match:
            continue

        waarde = match.group(1)

        if "," in waarde and "." in waarde:
            waarde = (
                waarde
                .replace(".", "")
                .replace(",", ".")
            )

        elif "," in waarde:
            waarde = waarde.replace(",", ".")

        elif waarde.count(".") > 1:
            waarde = waarde.replace(".", "")

        try:
            return float(waarde)

        except ValueError:
            continue

    return None


# ============================================================
# 2DEHANDS ZOEKEN
# ============================================================

def zoek_2dehands(zoekterm):

    url = (
        "https://www.2dehands.be/q/zoeken/"
        f"?query={quote(zoekterm)}"
    )

    print(f"Zoeken: {zoekterm}")
    print(f"URL: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    resultaten = []

    for link in soup.find_all("a", href=True):

        href = link["href"]

        if "/v/" not in href:
            continue

        if "/a" not in href and "/m" not in href:
            continue

        titel = link.get_text(
            " ",
            strip=True,
        )

        if not titel:
            continue

        if href.startswith("/"):
            href = (
                "https://www.2dehands.be"
                + href
            )

        if any(
            item["link"] == href
            for item in resultaten
        ):
            continue

        resultaten.append(
            {
                "title": titel,
                "link": href,
                "summary": "",
            }
        )

        if len(resultaten) >= MAX_RESULTATEN:
            break

    print(
        f"{len(resultaten)} resultaten gevonden."
    )

    return resultaten


# ============================================================
# ADVERTENTIE VERWERKEN
# ============================================================

def verwerk_advertentie(
    entry,
    zoekterm,
    gezien,
    stuur_melding=True,
):

    advertentie_id = entry["link"]

    if advertentie_id in gezien:
        return False

    titel = entry.get(
        "title",
        "Zonder titel",
    )

    link = entry.get(
        "link",
        "",
    )

    samenvatting = entry.get(
        "summary",
        "",
    )

    volledige_tekst = (
        f"{titel}\n{samenvatting}"
    )

    prijs = vind_prijs(
        volledige_tekst
    )

    if stuur_melding:
        stuur_email(
            titel=titel,
            zoekterm=zoekterm,
            prijs=prijs,
            link=link,
            beschrijving=samenvatting,
        )

    gezien.add(
        advertentie_id
    )

    return True


# ============================================================
# HOOFDPROGRAMMA
# ============================================================

def main():

    print("JAMES BOND BOT GESTART")

    gezien = laad_gezien()

    eerste_run = not EERSTE_RUN_FILE.exists()

    totaal_nieuw = 0

    for zoekterm in ZOEKOPDRACHTEN:

        print(
            f"Zoeken naar: {zoekterm}"
        )

        try:

            resultaten = zoek_2dehands(
                zoekterm
            )

            for entry in resultaten:

                try:

                    nieuw = verwerk_advertentie(
                        entry,
                        zoekterm,
                        gezien,
                        stuur_melding=not eerste_run,
                    )

                    if nieuw:
                        totaal_nieuw += 1

                except Exception as fout:

                    print(
                        "Fout bij advertentie:",
                        fout,
                    )

        except Exception as fout:

            print(
                f"Fout bij zoekopdracht "
                f"'{zoekterm}': {fout}"
            )

    bewaar_gezien(gezien)

    if eerste_run:

        EERSTE_RUN_FILE.touch()

        print(
            "Eerste run voltooid. "
            "Bestaande advertenties zijn opgeslagen."
        )

    print(
        f"Klaar. {totaal_nieuw} "
        "nieuwe advertenties."
    )


if __name__ == "__main__":
    main()
