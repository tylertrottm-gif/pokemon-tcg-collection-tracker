from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Set Browser", page_icon="🗂️", layout="wide")

from src.database import get_collection
from src.pokemon_api import PokemonAPIError, get_cards_for_set, get_sets
from src.ui import (
    apply_theme,
    collection_map,
    paginate,
    render_card_grid,
    require_access,
    sidebar_branding,
)

apply_theme()
if not require_access():
    st.stop()
sidebar_branding()

st.title("🗂️ Set Browser")
st.caption("Browse a complete expansion set and filter cards by collection status, rarity, name, or card number.")

try:
    sets = get_sets()
except PokemonAPIError as exc:
    st.error(str(exc))
    st.stop()

series_options = ["All series"] + sorted({item.get("series") or "Unknown Series" for item in sets})
selected_series = st.sidebar.selectbox("Series", series_options)
filtered_sets = (
    sets
    if selected_series == "All series"
    else [s for s in sets if (s.get("series") or "Unknown Series") == selected_series]
)

set_ids = [str(item.get("id")) for item in filtered_sets]
set_lookup = {str(item.get("id")): item for item in filtered_sets}
selected_set_id = st.selectbox(
    "Expansion set",
    set_ids,
    format_func=lambda set_id: (
        f"{set_lookup[set_id].get('name', 'Unknown Set')} "
        f"({str(set_lookup[set_id].get('releaseDate', ''))[:4]})"
    ),
)
selected_set = set_lookup[selected_set_id]

header_logo, header_text = st.columns([1, 4])
with header_logo:
    logo = (selected_set.get("images") or {}).get("logo")
    if logo:
        st.image(logo, width="stretch")
with header_text:
    st.subheader(selected_set.get("name", "Expansion Set"))
    st.caption(
        f"Series: {selected_set.get('series', 'Unknown')} · Released: {selected_set.get('releaseDate', 'Unknown')} · "
        f"Cards: {selected_set.get('total', 'Unknown')}"
    )

try:
    with st.spinner("Loading cards for this set..."):
        cards = get_cards_for_set(selected_set_id)
except PokemonAPIError as exc:
    st.error(str(exc))
    st.stop()

collection = get_collection()
owned_by_id = collection_map(collection)
set_owned = sum(1 for card in cards if str(card["id"]) in owned_by_id)
completion = set_owned / len(cards) if cards else 0

metric_a, metric_b, metric_c = st.columns(3)
metric_a.metric("Owned", f"{set_owned:,}")
metric_b.metric("Missing", f"{max(0, len(cards) - set_owned):,}")
metric_c.metric("Completion", f"{completion:.1%}")
st.progress(completion)

st.divider()
filter_a, filter_b, filter_c = st.columns([1, 1, 2])
with filter_a:
    status = st.selectbox("Collection status", ["All cards", "Owned", "Missing"])
with filter_b:
    rarities = sorted({card.get("rarity") or "Rarity not listed" for card in cards})
    selected_rarities = st.multiselect("Rarity", rarities)
with filter_c:
    search = st.text_input("Search card name or number", placeholder="Example: Charizard or 174")

visible_cards = cards
if status == "Owned":
    visible_cards = [card for card in visible_cards if str(card["id"]) in owned_by_id]
elif status == "Missing":
    visible_cards = [card for card in visible_cards if str(card["id"]) not in owned_by_id]

if selected_rarities:
    visible_cards = [
        card for card in visible_cards if (card.get("rarity") or "Rarity not listed") in selected_rarities
    ]

search_text = search.strip().casefold()
if search_text:
    visible_cards = [
        card
        for card in visible_cards
        if search_text in str(card.get("name", "")).casefold()
        or search_text in str(card.get("number", "")).casefold()
    ]

paged_cards = paginate(visible_cards, key=f"browser_{selected_set_id}")
render_card_grid(paged_cards, owned_by_id, page_key=f"browser_{selected_set_id}")
