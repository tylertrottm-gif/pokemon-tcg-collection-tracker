from __future__ import annotations

import re
from typing import Any

import requests
import streamlit as st

API_BASE_URL = "https://api.pokemontcg.io/v2"
REQUEST_TIMEOUT_SECONDS = 30


class PokemonAPIError(RuntimeError):
    """Raised when the Pokémon TCG API cannot fulfill a request."""


def _api_key() -> str:
    try:
        return str(st.secrets.get("pokemon_tcg", {}).get("api_key", "")).strip()
    except (FileNotFoundError, KeyError, TypeError):
        return ""


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    key = _api_key()
    if key:
        headers["X-Api-Key"] = key
    return headers


def _request(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.get(
            f"{API_BASE_URL}/{endpoint}",
            params=params,
            headers=_headers(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise PokemonAPIError(
            "The Pokémon TCG API could not be reached. Check the API key and try again."
        ) from exc
    except ValueError as exc:
        raise PokemonAPIError("The Pokémon TCG API returned an invalid response.") from exc


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def get_sets() -> list[dict[str, Any]]:
    """Return all sets, newest first, following API pagination."""
    page = 1
    page_size = 250
    all_sets: list[dict[str, Any]] = []

    while True:
        payload = _request(
            "sets",
            {
                "page": page,
                "pageSize": page_size,
                "orderBy": "-releaseDate",
                "select": "id,name,series,printedTotal,total,releaseDate,images",
            },
        )
        batch = payload.get("data", [])
        all_sets.extend(batch)

        total_count = int(payload.get("totalCount", len(all_sets)))
        if not batch or len(all_sets) >= total_count:
            break
        page += 1

    return all_sets


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def get_cards_for_set(set_id: str) -> list[dict[str, Any]]:
    """Return every card in a set, following API pagination."""
    page = 1
    page_size = 250
    all_cards: list[dict[str, Any]] = []

    while True:
        payload = _request(
            "cards",
            {
                "q": f"set.id:{set_id}",
                "page": page,
                "pageSize": page_size,
                "select": "id,name,number,rarity,artist,images,set,supertype,subtypes",
            },
        )
        batch = payload.get("data", [])
        all_cards.extend(batch)

        total_count = int(payload.get("totalCount", len(all_cards)))
        if not batch or len(all_cards) >= total_count:
            break
        page += 1

    return sorted(all_cards, key=lambda card: natural_card_number_key(card.get("number", "")))


def natural_card_number_key(value: str) -> tuple[Any, ...]:
    """Sort card numbers naturally, including values such as GG36 and TG01."""
    parts = re.split(r"(\d+)", str(value).upper())
    return tuple(int(part) if part.isdigit() else part for part in parts)


def find_set(sets: list[dict[str, Any]], set_id: str) -> dict[str, Any] | None:
    return next((item for item in sets if item.get("id") == set_id), None)
