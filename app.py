from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Pokémon TCG Collection Tracker",
    page_icon="⚡",
    layout="wide",
)

from src.database import get_collection
from src.pokemon_api import PokemonAPIError, get_sets
from src.ui import apply_theme, require_access, sidebar_branding

apply_theme()
if not require_access():
    st.stop()
sidebar_branding()

st.title("⚡ Pokémon TCG Collection Tracker")
st.caption("A personal dashboard for tracking cards, quantities, missing cards, and expansion-set completion.")

try:
    sets = get_sets()
except PokemonAPIError as exc:
    st.error(str(exc))
    st.stop()

collection = get_collection()
sets_by_id = {item["id"]: item for item in sets}

unique_cards = len(collection)
total_copies = sum(int(item.get("quantity", 0)) for item in collection)
started_set_ids = {item.get("set_id") for item in collection if item.get("set_id")}

progress_rows = []
for set_id in started_set_ids:
    set_info = sets_by_id.get(set_id, {})
    total = int(set_info.get("total") or 0)
    owned = sum(1 for item in collection if item.get("set_id") == set_id)
    completion = owned / total if total else 0
    progress_rows.append(
        {
            "Set": set_info.get("name") or next(
                (item.get("set_name") for item in collection if item.get("set_id") == set_id),
                set_id,
            ),
            "Owned": owned,
            "Total": total,
            "Completion": completion,
        }
    )

completed_sets = sum(1 for row in progress_rows if row["Total"] and row["Owned"] >= row["Total"])
started_total_cards = sum(row["Total"] for row in progress_rows)
overall_completion = unique_cards / started_total_cards if started_total_cards else 0

metric_columns = st.columns(5)
metric_columns[0].metric("Unique cards", f"{unique_cards:,}")
metric_columns[1].metric("Total copies", f"{total_copies:,}")
metric_columns[2].metric("Sets started", f"{len(started_set_ids):,}")
metric_columns[3].metric("Completed sets", f"{completed_sets:,}")
metric_columns[4].metric("Started-set completion", f"{overall_completion:.1%}")

st.divider()
left, right = st.columns([1.3, 1])

with left:
    st.subheader("Set completion")
    if progress_rows:
        progress_df = pd.DataFrame(progress_rows).sort_values("Completion", ascending=False)
        chart_df = progress_df.head(12).copy()
        chart_df["Completion %"] = chart_df["Completion"] * 100
        figure = px.bar(
            chart_df,
            x="Completion %",
            y="Set",
            orientation="h",
            text="Completion %",
            hover_data={"Owned": True, "Total": True, "Completion %": ":.1f"},
        )
        figure.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        figure.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Completion percentage",
            yaxis_title=None,
            margin=dict(l=0, r=20, t=10, b=0),
        )
        st.plotly_chart(figure, width="stretch")
    else:
        st.info("Add your first card from the Set Browser to begin tracking progress.")

with right:
    st.subheader("Recently added")
    if collection:
        recent = collection[:8]
        for item in recent:
            card_col, text_col = st.columns([1, 2.2])
            with card_col:
                if item.get("image_small"):
                    st.image(item["image_small"], width="stretch")
            with text_col:
                st.markdown(f"**{item.get('card_name', 'Unknown Card')}**")
                st.caption(
                    f"{item.get('set_name', 'Unknown Set')} · #{item.get('card_number', '—')} · "
                    f"Quantity {item.get('quantity', 1)}"
                )
    else:
        st.info("Your recently added cards will appear here.")

st.divider()
st.subheader("Start here")
st.markdown(
    "Open **Set Browser** from the sidebar, choose an expansion set, and add cards to your collection. "
    "Use **My Collection** to manage owned cards and export a backup, then use **Set Progress** to see which sets are closest to completion."
)
