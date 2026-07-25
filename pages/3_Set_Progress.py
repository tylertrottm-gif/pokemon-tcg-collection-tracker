from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Set Progress", page_icon="📈", layout="wide")

from src.database import get_collection
from src.pokemon_api import PokemonAPIError, get_sets
from src.ui import apply_theme, require_access, sidebar_branding

apply_theme()
if not require_access():
    st.stop()
sidebar_branding()

st.title("📈 Set Progress")
st.caption("Compare completion across expansion sets based on unique cards owned.")

try:
    sets = get_sets()
except PokemonAPIError as exc:
    st.error(str(exc))
    st.stop()

collection = get_collection()
owned_counts: dict[str, int] = {}
for item in collection:
    set_id = str(item.get("set_id", ""))
    owned_counts[set_id] = owned_counts.get(set_id, 0) + 1

rows = []
for set_info in sets:
    set_id = str(set_info.get("id", ""))
    owned = owned_counts.get(set_id, 0)
    total = int(set_info.get("total") or 0)
    completion = owned / total if total else 0
    rows.append(
        {
            "Set": set_info.get("name", "Unknown Set"),
            "Series": set_info.get("series") or "Unknown Series",
            "Released": set_info.get("releaseDate", ""),
            "Owned": owned,
            "Missing": max(0, total - owned),
            "Total": total,
            "Completion": completion,
        }
    )

progress_df = pd.DataFrame(rows)

filter_a, filter_b = st.columns(2)
with filter_a:
    view = st.selectbox("Show", ["Started sets", "In progress", "Completed", "All sets"])
with filter_b:
    series_options = sorted(progress_df["Series"].dropna().unique().tolist())
    selected_series = st.multiselect("Series", series_options)

visible_df = progress_df.copy()
if view == "Started sets":
    visible_df = visible_df[visible_df["Owned"] > 0]
elif view == "In progress":
    visible_df = visible_df[(visible_df["Owned"] > 0) & (visible_df["Completion"] < 1)]
elif view == "Completed":
    visible_df = visible_df[(visible_df["Total"] > 0) & (visible_df["Completion"] >= 1)]

if selected_series:
    visible_df = visible_df[visible_df["Series"].isin(selected_series)]

visible_df = visible_df.sort_values(["Completion", "Owned"], ascending=[False, False])

if visible_df.empty:
    st.info("No expansion sets match these filters.")
    st.stop()

chart_df = visible_df.head(20).copy()
chart_df["Completion %"] = chart_df["Completion"] * 100
figure = px.bar(
    chart_df,
    x="Completion %",
    y="Set",
    orientation="h",
    hover_data={"Owned": True, "Missing": True, "Total": True, "Completion %": ":.1f"},
)
figure.update_layout(
    yaxis={"categoryorder": "total ascending"},
    xaxis_title="Completion percentage",
    yaxis_title=None,
    margin=dict(l=0, r=20, t=20, b=0),
)
st.plotly_chart(figure, width="stretch")

st.dataframe(
    visible_df,
    width="stretch",
    hide_index=True,
    column_config={
        "Completion": st.column_config.ProgressColumn(
            "Completion",
            min_value=0,
            max_value=1,
            format="percent",
        ),
        "Released": st.column_config.TextColumn("Released"),
    },
)
