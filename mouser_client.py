# ============================================================
# Mouser Client (FINAL VERSION)
# ============================================================
import requests, time, random, json
from typing import Any, Dict, List, Optional, Tuple

MAX_RETRIES = 5
TIMEOUT = 10
BACKOFF_BASE = 1.5
BACKOFF_CAP = 4.0

session = requests.Session()

# Very lightweight global rate limiter (optional)
class RateLimiter:
    def __init__(self, per_sec: float = 3):
        self.delay = 1.0 / per_sec
        self.last_call = 0.0

    def wait(self):
        now = time.time()
        diff = now - self.last_call
        if diff < self.delay:
            time.sleep(self.delay - diff)
        self.last_call = time.time()

rate_limiter = RateLimiter(3)


class MouserClient:
    SEARCH_URL = "https://api.mouser.com/api/v1/search/partnumber"

    def __init__(self, api_key: Optional[str]):
        self.api_key = (api_key or "").strip()

        # In-memory cache { mpn → (main_data, alternates, error) }
        self.cache: Dict[str, Tuple[
            Optional[Dict[str, Any]],
            List[str],
            Optional[str]
        ]] = {}

    # ============================================================
    # Internal helpers
    # ============================================================
    def _backoff_sleep(self, attempt: int):
        delay = min(BACKOFF_CAP, (BACKOFF_BASE ** attempt)) + random.random() * 0.25
        time.sleep(delay)

    def _post_once(self, mpn: str) -> requests.Response:
        rate_limiter.wait()
        return session.post(
            self.SEARCH_URL,
            params={"apiKey": self.api_key},
            json={"SearchByPartRequest": {"mouserPartNumber": mpn}},
            timeout=TIMEOUT,
        )

    # ============================================================
    # Public API
    # ============================================================
    def search_part(self, mpn: str) -> Tuple[
        Optional[Dict[str, Any]],
        List[str],
        Optional[str]
    ]:
        """
        Returns tuple: (main_data, alternates, error)

        main_data = {
            "price": str|None,
            "manufacturer": str|None,
            "stock": str|None,
            "lifecycle": str|None
        }
        alternates = [mpn1, mpn2, ...]
        error = string or None
        """
        key = (mpn or "").strip()

        # ✅ Cache lookup
        if key in self.cache:
            return self.cache[key]

        # ✅ Missing API key
        if not self.api_key:
            result = (None, [], "Missing MOUSER_API_KEY")
            self.cache[key] = result
            return result

        last_exc: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            # ======================================================
            # Perform the POST request
            # ======================================================
            try:
                resp = self._post_once(key)
            except Exception as e:
                last_exc = e
                self._backoff_sleep(attempt)
                continue

            # ======================================================
            # GOOD RESPONSE (HTTP 200)
            # ======================================================
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except json.JSONDecodeError:
                    result = (None, [], "Invalid JSON response from Mouser")
                    self.cache[key] = result
                    return result

                parts = data.get("SearchResults", {}).get("Parts", []) or []

                # ✅ No results found
                if not parts:
                    result = (None, [], "No results")
                    self.cache[key] = result
                    return result

                # ==================================================
                # ✅ MAIN PART (FIRST RESULT)
                # ==================================================
                main = parts[0]

                alternates = [
                    (p.get("ManufacturerPartNumber") or "").strip()
                    for p in parts[1:]
                    if p.get("ManufacturerPartNumber")
                ]

                # Correct pricing structure
                price_breaks = main.get("PriceBreaks", []) or []
                unit_price = price_breaks[0].get("Price") if price_breaks else None

                main_data = {
                    "price": unit_price,
                    "manufacturer": main.get("Manufacturer"),
                    "stock": main.get("Availability"),
                    "lifecycle": main.get("LifecycleStatus"),
                }

                result = (main_data, alternates, None)
                self.cache[key] = result
                return result

            # ======================================================
            # HANDLE RATE-LIMIT OR TOO MANY REQUESTS
            # ======================================================
            if resp.status_code in (403, 429):
                try:
                    body = resp.json()
                except Exception:
                    body = {}

                err_list = body.get("Errors") or []
                err_code = (err_list[0] or {}).get("Code") if err_list else None

                if err_code == "TooManyRequests":
                    self._backoff_sleep(attempt)
                    continue

            # ======================================================
            # OTHER HTTP ERRORS
            # ======================================================
            err_snippet = (resp.text or "").strip()[:300]
            result = (None, [], f"HTTP {resp.status_code}: {err_snippet}")
            self.cache[key] = result
            return result

        # ==========================================================
        # EXHAUSTED RETRIES
        # ==========================================================
        if last_exc is not None:
            result = (None, [], f"Network error: {last_exc}")
            self.cache[key] = result
            return result

        result = (None, [], "Request failed after retries")
        self.cache[key] = result
        return result
