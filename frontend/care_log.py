from datetime import date

import streamlit as st

import plant_api
import cached_api


def days_since_watered(last_watered: str | None) -> int | None:
    if not last_watered:
        return None
    try:
        return (date.today() - date.fromisoformat(last_watered)).days
    except ValueError:
        return None


def render():
    st.markdown("# 📋 Care Log")
    st.caption("Track watering schedules and spot overdue plants at a glance.")

    plants = cached_api.get_plants()

    if not plants:
        st.info("No plants yet. Head to the Dashboard to add some!")
        return

    # -----------------------------------------------------------------------
    # Overdue alerts
    # -----------------------------------------------------------------------
    overdue = []
    for p in plants:
        days = days_since_watered(p.get("last_watered"))
        if days is not None and days > p.get("water_frequency_days", 7):
            overdue.append({**p, "_days_overdue": days - p["water_frequency_days"]})

    if overdue:
        st.markdown("### ⚠️ Overdue Plants")
        overdue.sort(key=lambda x: x["_days_overdue"], reverse=True)
        for p in overdue:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 3, 2])
                with c1:
                    st.markdown(f"**{p['name']}** — _{p['species']}_")
                with c2:
                    st.error(
                        f"Overdue by **{p['_days_overdue']}** day(s)  "
                        f"(last watered: {p.get('last_watered', 'never')})"
                    )
                with c3:
                    if st.button(
                        "💧 Water Now",
                        key=f"care_water_{p['id']}",
                        use_container_width=True,
                    ):
                        plant_api.patch_plant(
                            p["id"], {"last_watered": date.today().isoformat()}
                        )
                        cached_api.clear_cache()
                        st.rerun()
        st.divider()

    # -----------------------------------------------------------------------
    # Full schedule table
    # -----------------------------------------------------------------------
    st.markdown("### 🗓️ Watering Schedule")

    rows = []
    for p in plants:
        days = days_since_watered(p.get("last_watered"))
        next_in = (
            max(0, p.get("water_frequency_days", 7) - days) if days is not None else None
        )
        rows.append(
            {
                "Name": p["name"],
                "Species": p["species"],
                "Location": p["location"],
                "Frequency (days)": p["water_frequency_days"],
                "Last Watered": p.get("last_watered") or "Never",
                "Days Since": days if days is not None else "—",
                "Next In (days)": next_in if next_in is not None else "—",
                "Status": "⚠️ OVERDUE" if (days is not None and days > p["water_frequency_days"]) else "✅ OK",
            }
        )

    st.dataframe(rows, use_container_width=True, hide_index=True)
