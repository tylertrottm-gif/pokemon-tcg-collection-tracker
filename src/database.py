from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import streamlit as st
from supabase import Client, create_client

TABLE_NAME = "collection_items"
PAGE_SIZE = 1000


def _credentials() -> tuple[str, str]:
    try:
        section = st.secrets.get("supabase", {})
        return str(section.get("url", "")).strip(), str(section.get("key", "")).strip()
    except (FileNotFoundError, KeyError, TypeError):
        return "", ""


def database_available() -> bool:
    url, key = _credentials()
    return bool(url and key)


@st.cache_resource(show_spinner=False)
def get_client() -> Client | None:
    url, key = _credentials()
    if not url or not key:
        return None
    return create_client(url, key)


def _demo_collection() -> dict[str, dict[str, Any]]:
    if "demo_collection" not in st.session_state:
        st.session_state.demo_collection = {}
    return st.session_state.demo_collection


def get_collection() -> list[dict[str, Any]]:
    """Read the complete collection, paginating past Supabase's default limit."""
    client = get_client()
    if client is None:
        rows = list(_demo_collection().values())
        return sorted(rows, key=lambda row: row.get("date_added", ""), reverse=True)

    all_rows: list[dict[str, Any]] = []
    start = 0

    while True:
        response = (
            client.table(TABLE_NAME)
            .select("*")
            .order("date_added", desc=True)
            .range(start, start + PAGE_SIZE - 1)
            .execute()
        )
        batch = response.data or []
        all_rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        start += PAGE_SIZE

    return all_rows


def upsert_card(card: dict[str, Any], quantity: int) -> None:
    quantity = int(quantity)
    if quantity <= 0:
        delete_card(str(card["id"]))
        return

    card_set = card.get("set", {}) or {}
    images = card.get("images", {}) or {}
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "card_id": str(card["id"]),
        "card_name": str(card.get("name", "Unknown Card")),
        "set_id": str(card_set.get("id", "")),
        "set_name": str(card_set.get("name", "Unknown Set")),
        "card_number": str(card.get("number", "")),
        "rarity": card.get("rarity"),
        "image_small": images.get("small"),
        "quantity": quantity,
        "updated_at": now,
    }

    client = get_client()
    if client is None:
        demo = _demo_collection()
        if row["card_id"] not in demo:
            row["date_added"] = now
        else:
            row["date_added"] = demo[row["card_id"]].get("date_added", now)
        demo[row["card_id"]] = row
        return

    client.table(TABLE_NAME).upsert(row, on_conflict="card_id").execute()


def update_saved_quantity(card_id: str, quantity: int) -> None:
    quantity = int(quantity)
    if quantity <= 0:
        delete_card(card_id)
        return

    now = datetime.now(timezone.utc).isoformat()
    client = get_client()
    if client is None:
        demo = _demo_collection()
        if card_id in demo:
            demo[card_id]["quantity"] = quantity
            demo[card_id]["updated_at"] = now
        return

    (
        client.table(TABLE_NAME)
        .update({"quantity": quantity, "updated_at": now})
        .eq("card_id", card_id)
        .execute()
    )


def delete_card(card_id: str) -> None:
    client = get_client()
    if client is None:
        _demo_collection().pop(card_id, None)
        return

    client.table(TABLE_NAME).delete().eq("card_id", card_id).execute()
