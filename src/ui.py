from __future__ import annotations

import hashlib
import hmac
from typing import Any, Callable

import streamlit as st

from src.database import database_available, delete_card, update_saved_quantity, upsert_card


CUSTOM_CSS = """
<style>
.block-container {padding-top: 2rem; padding-bottom: 4rem;}
[data-testid="stMetric"] {
    background: rgba(31, 41, 55, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px;
}
.card-meta {min-height: 88px;}
.small-muted {color: #9CA3AF; font-size: 0.86rem;}
</style>
"""


def apply_theme() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def _configured_pin() -> str:
    try:
        return str(st.secrets.get("app", {}).get("owner_pin", "")).strip()
    except (FileNotFoundError, KeyError, TypeError):
        return ""


def require_access() -> bool:
    """Optionally protect the app with an owner PIN stored in Streamlit secrets."""
    configured_pin = _configured_pin()
    if not configured_pin:
        return True

    if st.session_state.get("authenticated", False):
        with st.sidebar:
            if st.button("Lock app", width="stretch"):
                st.session_state.authenticated = False
                st.rerun()
        return True

    st.title("🔒 Pokémon TCG Collection Tracker")
    st.caption("Enter the owner PIN to open the collection.")
    entered_pin = st.text_input("Owner PIN", type="password")
    if st.button("Unlock", type="primary"):
        expected = hashlib.sha256(configured_pin.encode("utf-8")).digest()
        received = hashlib.sha256(entered_pin.encode("utf-8")).digest()
        if hmac.compare_digest(expected, received):
            st.session_state.authenticated = True
            st.rerun()
        st.error("That PIN is not correct.")
    return False


def sidebar_branding() -> None:
    with st.sidebar:
        st.header("⚡ Collection Tracker")
        st.caption("Track owned cards, missing cards, quantities, and set completion.")
        st.divider()
        if database_available():
            st.success("Persistent storage configured", icon="☁️")
        else:
            st.warning("Demo mode: changes last only for this browser session", icon="🧪")


def collection_map(collection: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["card_id"]): item for item in collection}


def card_from_saved_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["card_id"],
        "name": item.get("card_name", "Unknown Card"),
        "number": item.get("card_number", ""),
        "rarity": item.get("rarity"),
        "images": {"small": item.get("image_small")},
        "set": {"id": item.get("set_id", ""), "name": item.get("set_name", "")},
    }


def render_card_grid(
    cards: list[dict[str, Any]],
    owned_by_id: dict[str, dict[str, Any]],
    *,
    page_key: str,
    columns_per_row: int = 4,
    on_change: Callable[[], None] | None = None,
) -> None:
    """Render card images and collection controls in a responsive grid."""
    if not cards:
        st.info("No cards match the selected filters.")
        return

    for start in range(0, len(cards), columns_per_row):
        columns = st.columns(columns_per_row)
        for offset, card in enumerate(cards[start : start + columns_per_row]):
            card_id = str(card["id"])
            saved = owned_by_id.get(card_id)
            quantity = int(saved.get("quantity", 0)) if saved else 0
            image_url = (card.get("images") or {}).get("small")
            rarity = card.get("rarity") or "Rarity not listed"
            number = card.get("number") or "—"

            with columns[offset]:
                if image_url:
                    st.image(image_url, width="stretch")
                else:
                    st.info("Image unavailable")

                st.markdown(
                    f"<div class='card-meta'><strong>{card.get('name', 'Unknown Card')}</strong><br>"
                    f"<span class='small-muted'>#{number} · {rarity}</span><br>"
                    f"<span>{'✅ Owned: ' + str(quantity) if quantity else '⬜ Missing'}</span></div>",
                    unsafe_allow_html=True,
                )

                if quantity == 0:
                    if st.button(
                        "Add to collection",
                        key=f"{page_key}_add_{card_id}",
                        type="primary",
                        width="stretch",
                    ):
                        upsert_card(card, 1)
                        st.toast(f"Added {card.get('name', 'card')} to the collection.")
                        if on_change:
                            on_change()
                        st.rerun()
                else:
                    left, middle, right = st.columns(3)
                    if left.button("−", key=f"{page_key}_minus_{card_id}", width="stretch"):
                        update_saved_quantity(card_id, quantity - 1)
                        if on_change:
                            on_change()
                        st.rerun()
                    if middle.button("+", key=f"{page_key}_plus_{card_id}", width="stretch"):
                        update_saved_quantity(card_id, quantity + 1)
                        if on_change:
                            on_change()
                        st.rerun()
                    if right.button("✕", key=f"{page_key}_delete_{card_id}", width="stretch"):
                        delete_card(card_id)
                        st.toast(f"Removed {card.get('name', 'card')} from the collection.")
                        if on_change:
                            on_change()
                        st.rerun()


def paginate(items: list[Any], *, key: str, default_size: int = 24) -> list[Any]:
    size_options = [12, 24, 48]
    default_index = size_options.index(default_size) if default_size in size_options else 1
    control_a, control_b = st.columns([1, 2])
    with control_a:
        page_size = st.selectbox(
            "Cards per page",
            size_options,
            index=default_index,
            key=f"{key}_page_size",
        )

    total_pages = max(1, (len(items) + page_size - 1) // page_size)
    page_state_key = f"{key}_page"
    current_page = int(st.session_state.get(page_state_key, 1))
    st.session_state[page_state_key] = max(1, min(current_page, total_pages))
    with control_b:
        page_number = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            step=1,
            key=page_state_key,
        )

    start = (int(page_number) - 1) * page_size
    end = start + page_size
    st.caption(f"Showing {start + 1 if items else 0}–{min(end, len(items))} of {len(items)} cards")
    return items[start:end]
