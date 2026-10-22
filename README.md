# britwatch

Android-app (PWA) som visar allt som finns på BritBox i Sverige, så att man
kan söka upp titlarna på Tele2 TV-hubben.

- `index.html` – appen (sök, filter, sortering, markera som kollad)
- `data.json` – utbudet, hämtas från JustWatch
- `scripts/hamta.py` – hämtar ny data (`python scripts/hamta.py`)
- `.github/workflows/hamta-data.yml` – kör hämtningen varje natt på GitHub
