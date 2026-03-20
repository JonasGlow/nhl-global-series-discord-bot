import json
import logging
from dataclasses import dataclass
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from nhl_global_series_discord_bot.utils.config import settings

log = logging.getLogger(__name__)

STATE_FILE = Path("state.json")

# Live Nation event pages for both Düsseldorf games
LIVE_NATION_EVENTS = [
    {
        "url": "https://www.livenation.de/event/nhl-global-series-d%C3%BCsseldorf-d%C3%BCsseldorf-tickets-edp1659803",
        "name": "NHL Global Series Düsseldorf – Game 1 (Dec 18)",
        "date": "December 18, 2026",
        "state_key": "ln_dusseldorf_game1",
    },
    {
        "url": "https://www.livenation.de/event/nhl-global-series-d%C3%BCsseldorf-d%C3%BCsseldorf-tickets-edp1659804",
        "name": "NHL Global Series Düsseldorf – Game 2 (Dec 20)",
        "date": "December 20, 2026",
        "state_key": "ln_dusseldorf_game2",
    },
]

TICKETMASTER_API_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


@dataclass
class TicketResult:
    source: str
    event_name: str
    event_date: str
    url: str
    status: str  # z.B. "onsale", "available", "presale"
    price_info: str = ""


def _load_state() -> dict:
    if STATE_FILE.exists():
        content = STATE_FILE.read_text().strip()
        if content:
            return json.loads(content)
    return {}


def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _is_new(key: str, value: str, state: dict) -> bool:
    """Gibt True zurück wenn sich der Wert geändert hat oder neu ist."""
    return state.get(key) != value


class TicketChecker:
    def __init__(self):
        self.state = _load_state()

    async def check_all(self) -> list[TicketResult]:
        results = []
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            # Ticketmaster API (primary source)
            tm_results = await self._check_ticketmaster(client)
            results.extend(tm_results)

            # Live Nation scraper (backup) – check both games
            for event in LIVE_NATION_EVENTS:
                ln_result = await self._check_live_nation(client, event)
                if ln_result:
                    results.append(ln_result)

        _save_state(self.state)
        return results

    async def _check_ticketmaster(self, client: httpx.AsyncClient) -> list[TicketResult]:
        """Fragt die Ticketmaster Discovery API ab."""
        params = {
            "apikey": settings.ticketmaster_api_key,
            "keyword": settings.tm_keyword,
            "city": settings.tm_city,
            "countryCode": settings.tm_country_code,
            "classificationName": "sports",
            "size": 10,
        }

        try:
            resp = await client.get(TICKETMASTER_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log.error(f"Ticketmaster API Fehler: {e}")
            return []

        events = data.get("_embedded", {}).get("events", [])
        if not events:
            log.info("Ticketmaster: Keine Events gefunden.")
            return []

        results = []
        for event in events:
            name = event.get("name", "Unbekanntes Event")
            event_id = event.get("id", name)
            url = event.get("url", "")
            dates = event.get("dates", {})
            date_str = dates.get("start", {}).get("localDate", "unbekannt")
            status = dates.get("status", {}).get("code", "unknown")

            # Preisinformationen (falls vorhanden)
            price_info = ""
            price_ranges = event.get("priceRanges", [])
            if price_ranges:
                p = price_ranges[0]
                price_info = f"{p.get('min', '?')}–{p.get('max', '?')} {p.get('currency', 'EUR')}"

            state_key = f"tm_{event_id}"
            state_value = f"{status}|{price_info}"

            if _is_new(state_key, state_value, self.state):
                log.info(f"Ticketmaster: Neue Info für '{name}' – Status: {status}")
                self.state[state_key] = state_value
                results.append(
                    TicketResult(
                        source="Ticketmaster",
                        event_name=name,
                        event_date=date_str,
                        url=url,
                        status=status,
                        price_info=price_info,
                    )
                )

        return results

    async def _check_live_nation(self, client: httpx.AsyncClient, event: dict) -> TicketResult | None:
        """Scrapes a Live Nation event page as backup."""
        try:
            resp = await client.get(event["url"], headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except Exception as e:
            log.error(f"Live Nation scraper error for {event['name']}: {e}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Look for ticket status button
        status_text = "unknown"
        for btn in soup.find_all(["button", "a"]):
            text = btn.get_text(strip=True).lower()
            if any(kw in text for kw in ["ticket", "kaufen", "registrieren", "unavailable", "sold out"]):
                status_text = text
                break

        if _is_new(event["state_key"], status_text, self.state):
            log.info(f"Live Nation: Status changed to '{status_text}' for {event['name']}")
            self.state[event["state_key"]] = status_text
            return TicketResult(
                source="Live Nation",
                event_name=event["name"],
                event_date=event["date"],
                url=event["url"],
                status=status_text,
            )

        return None