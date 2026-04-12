from datetime import datetime, timezone

import streamlit as st

import plant_api
import cached_api


def hours_since_watered(last_watered: str | None) -> float | None:
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


def render():
    st.markdown("# 📋 Care Log")
    st.caption("Track watering schedules and spot overdue plants at a glance.")

    plants = cached_api.get_plants()

    if not plants:
        st.info("No plants yet. Head to the Dashboard to add some!")
        return

    # -------------------------------------------------------------------
    # Summary metrics
    # -------------------------------------------------------------------
    overdue_plants = []
    healthy_count = 0
    attention_count = 0
    critical_count = 0
    watered_recently = 0

    for p in plants:
        hours = hours_since_watered(p.get("last_watered"))
        freq = p.get("water_frequency_hours", 168)
        if hours is not None and hours > freq:
            overdue_plants.append({**p, "_hours_overdue": hours - freq})
        if p.get("health_status") == "healthy":
            healthy_count += 1
        elif p.get("health_status") == "needs_attention":
            attention_count += 1
        elif p.get("health_status") == "critical":
            critical_count += 1
        if hours is not None and hours < 1:
            watered_recently += 1

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🌿 Healthy", healthy_count)
    m2.metric("🟡 Needs Attention", attention_count)
    m3.metric("🔴 Critical", critical_count)
    m4.metric("💧 Watered Recently", watered_recently)

    st.divider()

    # -------------------------------------------------------------------
    # Overdue alerts
    # -------------------------------------------------------------------
    if overdue_plants:
        st.markdown("### ⚠️ Overdue — Need Watering")
        overdue_plants.sort(key=lambda x: x["_hours_overdue"], reverse=True)
        for p in overdue_plants:
            hrs = p["_hours_overdue"]
            if hrs < 24:
                overdue_text = f"{int(hrs)}h overdue"
            else:
                overdue_text = f"{int(hrs / 24)} day(s) overdue"

            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 3, 2])
                with c1:
                    st.markdown(f"**{p['name']}** — _{p['species']}_")
                with c2:
                    st.error(
                        f"**{overdue_text}**  "
                        f"(last watered: {p.get('last_watered', 'never')[:16]})"
                    )
                with c3:
                    if st.button(
                        "💧 Water Now",
                        key=f"care_water_{p['id']}",
                        use_container_width=True,
                    ):
                        plant_api.patch_plant(
                            p["id"],
                            {"last_watered": datetime.now(timezone.utc).isoformat()},
                        )
                        cached_api.clear_cache()
                        st.rerun()
        st.divider()
    else:
        st.success("All plants are on schedule! No overdue watering.", icon="✅")
        st.divider()

    # -------------------------------------------------------------------
    # Full schedule table
    # -------------------------------------------------------------------
    st.markdown("### 🗓️ Watering Schedule")

    rows = []
    for p in plants:
        hours = hours_since_watered(p.get("last_watered"))
        freq = p.get("water_frequency_hours", 168)
        next_in_hrs = max(0, freq - hours) if hours is not None else None

        health = p.get("health_status", "unknown")
        health_display = {
            "healthy": "🟢 Healthy",
            "needs_attention": "🟡 Attention",
            "critical": "🔴 Critical",
        }.get(health, health)

        if hours is not None and hours > freq:
            water_status = "⚠️ OVERDUE"
        elif hours is not None and hours < 1:
            water_status = "💧 Just watered"
        else:
            water_status = "✅ OK"

        def fmt_hours(h):
            if h is None:
                return "—"
            if h < 1:
                return f"{int(h * 60)} min"
            if h < 24:
                return f"{int(h)}h"
            return f"{int(h / 24)}d {int(h % 24)}h"

        rows.append(
            {
                "Name": p["name"],
                "Species": p["species"],
                "Location": p["location"],
                "Health": health_display,
                "Every": fmt_hours(freq),
                "Last Watered": (p.get("last_watered") or "Never")[:16],
                "Ago": fmt_hours(hours),
                "Next In": fmt_hours(next_in_hrs),
                "Status": water_status,
            }
        )

    st.dataframe(rows, use_container_width=True, hide_index=True)
