from __future__ import annotations

import pandas as pd
import streamlit as st

st.set_page_config(page_title="My Collection", page_icon="📚", layout="wide")

from src.database import get_collection
from src.ui import (
    apply_theme,
    card_from_saved_item,
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

st.title("📚 My Collection")
st.caption("Review owned cards, manage duplicate quantities, and export a CSV backup.")

collection = get_collection()
if not collection:
    st.info("No cards have been added yet. Open Set Browser to start your collection.")
    st.stop()

unique_cards = len(collection)
total_copies = sum(int(item.get("quantity", 0)) for item in collection)
sets_started = len({item.get("set_id") for item in collection})
duplicate_copies = max(0, total_copies - unique_cards)

metrics = st.columns(4)
metrics[0].metric("Unique cards", f"{unique_cards:,}")
metrics[1].metric("Total copies", f"{total_copies:,}")
metrics[2].metric("Sets represented", f"{sets_started:,}")
metrics[3].metric("Duplicate copies", f"{duplicate_copies:,}")

export_columns = [
    "card_name",
    "set_name",
    "card_number",
    "rarity",
    "quantity",
    "date_added",
    "updated_at",
]
export_df = pd.DataFrame(collection)
for column in export_columns:
    if column not in export_df.columns:
        export_df[column] = ""

st.download_button(
    "Download collection CSV",
    data=export_df[export_columns].to_csv(index=False).encode("utf-8"),
    file_name="pokemon_tcg_collection.csv",
    mime="text/csv",
)

st.divider()
filter_a, filter_b, filter_c = st.columns([1, 1, 2])
with filter_a:
    set_names = sorted({item.get("set_name", "Unknown Set") for item in collection})
    selected_sets = st.multiselect("Expansion set", set_names)
with filter_b:
    rarities = sorted({item.get("rarity") or "Rarity not listed" for item in collection})
    selected_rarities = st.multiselect("Rarity", rarities)
with filter_c:
    search = st.text_input("Search card name or number")

visible_items = collection
if selected_sets:
    visible_items = [item for item in visible_items if item.get("set_name") in selected_sets]
if selected_rarities:
    visible_items = [
        item for item in visible_items if (item.get("rarity") or "Rarity not listed") in selected_rarities
    ]

search_text = search.strip().casefold()
if search_text:
    visible_items = [
        item
        for item in visible_items
        if search_text in str(item.get("card_name", "")).casefold()
        or search_text in str(item.get("card_number", "")).casefold()
    ]

cards = [card_from_saved_item(item) for item in visible_items]
owned_by_id = collection_map(collection)
paged_cards = paginate(cards, key="my_collection")
render_card_grid(paged_cards, owned_by_id, page_key="my_collection")
