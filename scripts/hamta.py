# Hämtar allt som finns på BritBox i Sverige från JustWatch och sparar det
# i data.json. Körs automatiskt av GitHub Actions (se .github/workflows/).
# Använder bara Pythons standardbibliotek, så inget behöver installeras.

import json
import pathlib
import time
import urllib.request
from datetime import datetime, timezone

API = "https://apis.justwatch.com/graphql"
LAND = "SE"
SPRAK = "sv"
TJANST = "bbo"  # JustWatch kortnamn för BritBox
UT = pathlib.Path(__file__).resolve().parent.parent / "data.json"

FRAGA = """
query($after: String) {
  popularTitles(country: %(land)s, first: 40, after: $after,
                filter: {packages: ["%(tjanst)s"]}, sortBy: POPULAR) {
    totalCount
    pageInfo { endCursor hasNextPage }
    edges { node {
      id
      objectType
      content(country: %(land)s, language: "%(sprak)s") {
        title originalTitle originalReleaseYear shortDescription
        posterUrl fullPath
        genres { shortName }
        scoring { imdbScore }
      }
      ... on Show { totalSeasonCount }
      offers(country: %(land)s, platform: WEB, filter: {packages: ["%(tjanst)s"]}) { dateCreated }
    } }
  }
}
""" % {"land": LAND, "sprak": SPRAK, "tjanst": TJANST}


def hamta_sida(after):
    body = json.dumps({"query": FRAGA, "variables": {"after": after}}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "content-type": "application/json",
        "user-agent": "britwatch (privat app)",
    })
    with urllib.request.urlopen(req, timeout=30) as svar:
        data = json.load(svar)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]["popularTitles"]


def gor_om(node):
    c = node["content"]
    poster = c.get("posterUrl")
    datum = [o["dateCreated"] for o in node.get("offers") or [] if o.get("dateCreated")]
    return {
        "id": node["id"],
        "typ": "serie" if node["objectType"] == "SHOW" else "film",
        "titel": c["title"],
        "originaltitel": c.get("originalTitle"),
        "ar": c.get("originalReleaseYear"),
        "beskrivning": c.get("shortDescription"),
        "bild": "https://images.justwatch.com" + poster.replace("{profile}", "s166").replace("{format}", "webp") if poster else None,
        "lank": "https://www.justwatch.com" + c["fullPath"] if c.get("fullPath") else None,
        "genrer": [g["shortName"] for g in c.get("genres") or []],
        "imdb": (c.get("scoring") or {}).get("imdbScore"),
        "sasonger": node.get("totalSeasonCount"),
        "tillagd": min(datum) if datum else None,
    }


def main():
    titlar, after = [], None
    while True:
        sida = hamta_sida(after)
        titlar += [gor_om(e["node"]) for e in sida["edges"]]
        if not sida["pageInfo"]["hasNextPage"]:
            break
        after = sida["pageInfo"]["endCursor"]
        time.sleep(1)  # var snäll mot servern

    if not titlar:
        raise SystemExit("Fick inga titlar, behåller gamla data.json")

    UT.write_text(json.dumps({
        "uppdaterad": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "titlar": titlar,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Sparade {len(titlar)} titlar i {UT.name}")


if __name__ == "__main__":
    main()
