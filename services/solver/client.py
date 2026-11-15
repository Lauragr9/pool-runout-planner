import os
import time

import requests

LAYOUTS_URL = os.environ.get("LAYOUTS_URL", "http://layouts:8000")
LAYOUTS_TIMEOUT_S = float(os.environ.get("LAYOUTS_TIMEOUT_S", 2))
LAYOUTS_RETRIES = int(os.environ.get("LAYOUTS_RETRIES", 2))


class LayoutsUnavailable(Exception):
    """Raised when the layouts service can't be reached after retrying."""


def get_layout(layout_id):
    """Fetch {id, cue, balls} for layout_id from the layouts service, or
    None if that layout_id doesn't exist there.

    A short timeout plus a couple of retries with backoff covers a
    cold-starting container; if layouts is still unreachable after that,
    there's no sane way to solve blind, so this raises instead of
    returning some degraded result.
    """
    last_error = None
    for attempt in range(LAYOUTS_RETRIES + 1):
        try:
            response = requests.get(
                f"{LAYOUTS_URL}/layouts/{layout_id}", timeout=LAYOUTS_TIMEOUT_S
            )
        except requests.RequestException as error:
            last_error = error
            if attempt < LAYOUTS_RETRIES:
                time.sleep(0.5 * (attempt + 1))
            continue
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    raise LayoutsUnavailable(f"layouts service unreachable: {last_error}")
