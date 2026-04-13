import json
from datetime import datetime, timezone

import streamlit as st

import plant_api
import cached_api

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PlantPal",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css():
    import os

    css_path = os.path.join(os.path.dirname(__file__), "theme.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
LIGHT_ICONS = {"low": "🌑", "medium": "🌤️", "high": "☀️"}
HEALTH_BADGES = {
    "healthy": ("🟢", "Healthy"),
    "needs_attention": ("🟡", "Needs Attention"),
    "critical": ("🔴", "Critical"),
}


def hours_since_watered(last_watered: str | None) -> float | None:
    """Return hours elapsed since the ISO-8601 ``last_watered`` timestamp,
    or None if the value is missing or unparseable.  Naive datetimes are
    treated as UTC."""
    if not last_watered:
        return None
    try:
        watered = datetime.fromisoformat(last_watered)
        if watered.tzinfo is None:
            watered = watered.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - watered
        return delta.total_seconds() / 3600
    except ValueError:
        return None


def is_overdue(plant: dict) -> bool:
    """True when more hours have passed since the last watering than the
    plant's ``water_frequency_hours`` schedule allows."""
    hours = hours_since_watered(plant.get("last_watered"))
    if hours is None:
        return False
    return hours > plant.get("water_frequency_hours", 168)


def format_relative(last_watered: str | None) -> str:
    hours = hours_since_watered(last_watered)
    if hours is None:
        return "Never"
    if hours < 1:
        return f"{int(hours * 60)} min ago"
    if hours < 24:
        return f"{int(hours)}h ago"
    days = int(hours / 24)
    if days == 1:
        return "Yesterday"
    return f"{days} days ago"


def format_frequency(hours: int) -> str:
    if hours < 24:
        return f"Every {hours}h"
    days = hours / 24
    if days == int(days):
        return f"Every {int(days)} days"
    return f"Every {days:.1f} days"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌿 PlantPal")
    st.caption("Indoor Plant Care Tracker")
    st.divider()

    page = st.radio(
        "Navigate",
        ["Dashboard", "Care Log"],
        label_visibility="collapsed",
    )

    st.divider()
    backend_ok = plant_api.healthcheck()
    if backend_ok:
        st.success("Backend connected", icon="✅")
    else:
        st.error("Backend unreachable", icon="🚫")

    st.divider()
    st.markdown(
        "<div style='text-align:center; font-size:0.75rem; opacity:0.6;'>"
        "&copy; 2026 Roy Carter. All rights reserved."
        "</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Care Log page (delegated)
# ---------------------------------------------------------------------------
if page == "Care Log":
    st.session_state["_prev_page"] = "Care Log"
    import care_log

    care_log.render()
    st.stop()

# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------

if st.session_state.get("_prev_page") != "Dashboard":
    for key in list(st.session_state):
        if key.startswith(("editing_", "confirm_del_")):
            del st.session_state[key]
st.session_state["_prev_page"] = "Dashboard"

plants = cached_api.get_plants()

# -- Header row --
col_title, col_action = st.columns([4, 1])
with col_title:
    st.markdown("# 🌱 My Plants")
with col_action:
    if st.button("➕ Add Plant", use_container_width=True, type="primary"):
        st.session_state["show_add_form"] = True

# -- Metrics --
total = len(plants)
healthy = sum(1 for p in plants if p.get("health_status") == "healthy")
overdue_count = sum(1 for p in plants if is_overdue(p))

m1, m2, m3 = st.columns(3)
m1.metric("Total Plants 🌱", total)
m2.metric("Healthy 🟢", healthy)
m3.metric("Need Water 💧", overdue_count)

# ---------------------------------------------------------------------------
# Add Plant dialog
# ---------------------------------------------------------------------------
if st.session_state.get("show_add_form"):

    @st.dialog("Add a New Plant")
    def add_dialog():
        name = st.text_input("Name *")
        species = st.text_input("Species *")
        location = st.selectbox(
            "Location",
            ["Living Room", "Bedroom", "Kitchen", "Bathroom", "Balcony", "Office", "Other"],
        )
        light = st.select_slider("Light Need", options=["low", "medium", "high"], value="medium")
        freq = st.number_input("Water every (hours)", min_value=1, max_value=2160, value=168)
        health = st.selectbox("Health Status", ["healthy", "needs_attention", "critical"])
        notes = st.text_area("Notes", max_chars=300)

        if st.button("Save", type="primary", use_container_width=True):
            if not name or not species:
                st.error("Name and Species are required.")
                return
            try:
                plant_api.create_plant(
                    {
                        "name": name,
                        "species": species,
                        "location": location,
                        "light_need": light,
                        "water_frequency_hours": freq,
                        "health_status": health,
                        "notes": notes,
                    }
                )
                cached_api.clear_cache()
                st.session_state["show_add_form"] = False
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to create plant: {exc}")

    add_dialog()

# ---------------------------------------------------------------------------
# Search & Filter
# ---------------------------------------------------------------------------
st.divider()
fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 2])
with fc1:
    search = st.text_input("Search", placeholder="Search by name…")
with fc2:
    locations = sorted({p["location"] for p in plants})
    filter_loc = st.multiselect("Location", locations, placeholder="All locations")
with fc3:
    filter_health = st.multiselect(
        "Health", ["healthy", "needs_attention", "critical"], placeholder="All"
    )
with fc4:
    filter_light = st.multiselect("Light", ["low", "medium", "high"], placeholder="All")

filtered = plants
if search:
    filtered = [p for p in filtered if search.lower() in p["name"].lower()]
if filter_loc:
    filtered = [p for p in filtered if p["location"] in filter_loc]
if filter_health:
    filtered = [p for p in filtered if p["health_status"] in filter_health]
if filter_light:
    filtered = [p for p in filtered if p["light_need"] in filter_light]

# ---------------------------------------------------------------------------
# Plant table
# ---------------------------------------------------------------------------
if not filtered:
    st.info("No plants found. Add your first plant above!")
else:
    for plant in filtered:
        overdue = is_overdue(plant)
        health_icon, health_label = HEALTH_BADGES.get(
            plant["health_status"], ("⚪", plant["health_status"])
        )
        light_icon = LIGHT_ICONS.get(plant["light_need"], "")
        freq_hours = plant.get("water_frequency_hours", 168)

        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 3])

            with c1:
                label = f"**{plant['name']}**"
                if overdue:
                    label += " ⚠️"
                st.markdown(label)
                st.caption(f"_{plant['species']}_")

            with c2:
                st.markdown(f"{health_icon} {health_label}")
                st.caption(f"{light_icon} {plant['light_need']} light")

            with c3:
                st.markdown(f"📍 {plant['location']}")
                watered_text = format_relative(plant.get("last_watered"))
                if overdue:
                    st.caption(f"💧 Watered: **{watered_text}** — OVERDUE")
                else:
                    st.caption(f"💧 Watered: {watered_text}")

            with c4:
                st.markdown(format_frequency(freq_hours))
                if plant.get("notes"):
                    st.caption(plant["notes"][:60])

            with c5:
                bc1, bc2, bc3 = st.columns(3)
                with bc1:
                    if st.button("💧", key=f"water_{plant['id']}", help="Water now"):
                        plant_api.patch_plant(
                            plant["id"],
                            {"last_watered": datetime.now(timezone.utc).isoformat()},
                        )
                        cached_api.clear_cache()
                        st.rerun()
                with bc2:
                    if st.button("✏️", key=f"edit_{plant['id']}", help="Edit"):
                        st.session_state[f"editing_{plant['id']}"] = True
                        st.rerun()
                with bc3:
                    if st.button("🗑️", key=f"del_{plant['id']}", help="Delete"):
                        st.session_state[f"confirm_del_{plant['id']}"] = True
                        st.rerun()

        # -- Edit dialog --
        if st.session_state.get(f"editing_{plant['id']}"):

            @st.dialog(f"Edit {plant['name']}")
            def edit_dialog(p=plant):
                name = st.text_input("Name", value=p["name"])
                species = st.text_input("Species", value=p["species"])
                location = st.selectbox(
                    "Location",
                    ["Living Room", "Bedroom", "Kitchen", "Bathroom", "Balcony", "Office", "Other"],
                    index=["Living Room", "Bedroom", "Kitchen", "Bathroom", "Balcony", "Office", "Other"].index(p["location"])
                    if p["location"] in ["Living Room", "Bedroom", "Kitchen", "Bathroom", "Balcony", "Office", "Other"]
                    else 0,
                )
                light = st.select_slider(
                    "Light Need",
                    options=["low", "medium", "high"],
                    value=p["light_need"],
                )
                freq = st.number_input(
                    "Water every (hours)", min_value=1, max_value=2160, value=p["water_frequency_hours"]
                )
                health = st.selectbox(
                    "Health",
                    ["healthy", "needs_attention", "critical"],
                    index=["healthy", "needs_attention", "critical"].index(p["health_status"]),
                )
                notes = st.text_area("Notes", value=p.get("notes", ""), max_chars=300)

                if st.button("Save Changes", type="primary", use_container_width=True):
                    try:
                        plant_api.update_plant(
                            p["id"],
                            {
                                "name": name,
                                "species": species,
                                "location": location,
                                "light_need": light,
                                "water_frequency_hours": freq,
                                "last_watered": p.get("last_watered", ""),
                                "health_status": health,
                                "image_url": p.get("image_url", ""),
                                "notes": notes,
                            },
                        )
                        cached_api.clear_cache()
                        del st.session_state[f"editing_{p['id']}"]
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Update failed: {exc}")

            edit_dialog()

        # -- Delete confirmation --
        if st.session_state.get(f"confirm_del_{plant['id']}"):

            @st.dialog(f"Delete {plant['name']}?")
            def delete_dialog(p=plant):
                st.warning(f"Are you sure you want to delete **{p['name']}**? This cannot be undone.")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("Cancel", use_container_width=True):
                        del st.session_state[f"confirm_del_{p['id']}"]
                        st.rerun()
                with dc2:
                    if st.button("Delete", type="primary", use_container_width=True):
                        try:
                            plant_api.delete_plant(p["id"])
                            cached_api.clear_cache()
                            del st.session_state[f"confirm_del_{p['id']}"]
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Delete failed: {exc}")

            delete_dialog()

# ---------------------------------------------------------------------------
# Export to JSON (small extra)
# ---------------------------------------------------------------------------
st.divider()
if plants:
    st.download_button(
        "📥 Export to JSON",
        data=json.dumps(plants, indent=2),
        file_name="plantpal_export.json",
        mime="application/json",
    )
