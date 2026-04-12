from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

import streamlit as st

import plant_api
import cached_api

EVENT_ICONS = {
    "watered": "💧",
    "health_changed": "🩺",
    "edited": "✏️",
    "note": "📝",
}

EVENT_LABELS = {
    "watered": "Watered",
    "health_changed": "Health changed",
    "edited": "Edited",
    "note": "Note",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_dt(iso: str) -> datetime | None:
    """Safely parse an ISO-8601 string into a timezone-aware datetime.
    Returns None on bad input instead of raising."""
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _day_label(dt: datetime) -> str:
    today = datetime.now(timezone.utc).date()
    d = dt.date()
    if d == today:
        return "Today"
    if d == today - timedelta(days=1):
        return "Yesterday"
    return d.strftime("%b %d, %Y")


def _relative_time(dt: datetime) -> str:
    seconds = (datetime.now(timezone.utc) - dt).total_seconds()
    if seconds < 3600:
        return f"{int(seconds / 60)} min ago"
    if seconds < 86400:
        return f"{int(seconds / 3600)}h ago"
    return f"{int(seconds / 86400)}d ago"


def _compute_streak(events: list[dict]) -> int:
    """Count consecutive days (ending today or yesterday) with at least one watering."""
    water_dates = {
        _parse_dt(e["created_at"]).date()
        for e in events
        if e.get("event_type") == "watered" and _parse_dt(e.get("created_at", ""))
    }
    if not water_dates:
        return 0

    day = datetime.now(timezone.utc).date()
    # Allow streak to start from yesterday if nothing today yet
    if day not in water_dates:
        day -= timedelta(days=1)
    if day not in water_dates:
        return 0

    streak = 0
    while day in water_dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


def _consistency_label(water_events: list[dict], freq_hours: int) -> tuple[str, str]:
    """Rate how consistently a plant is watered vs. its schedule.

    Computes the average gap between consecutive waterings and compares
    it to the expected frequency:
      * ratio <= 1.1  ->  "On track"
      * ratio <= 1.5  ->  "Slightly late"
      * ratio >  1.5  ->  "Often late"

    Returns ``(label, tooltip)`` for display in the drilldown metrics.
    """
    count = len(water_events)
    if count == 0:
        return "No data yet", "Water this plant a few times to track your rhythm."
    if count == 1:
        return "Just started", "Water again to start building a pattern."

    dates = sorted(
        _parse_dt(e["created_at"])
        for e in water_events
        if _parse_dt(e["created_at"])
    )
    if len(dates) < 2:
        return "Just started", "Water again to start building a pattern."

    freq_days = freq_hours / 24
    gaps = [(dates[i] - dates[i - 1]).total_seconds() / 86400 for i in range(1, len(dates))]
    avg_gap = sum(gaps) / len(gaps)
    ratio = avg_gap / freq_days if freq_days > 0 else 0

    if ratio <= 1.1:
        return "On track", f"You water roughly every {avg_gap:.1f}d (schedule: every {freq_days:.0f}d)."
    if ratio <= 1.5:
        return "Slightly late", f"Avg gap is {avg_gap:.1f}d but schedule says every {freq_days:.0f}d."
    return "Often late", f"Avg gap is {avg_gap:.1f}d — schedule says every {freq_days:.0f}d."


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render():
    st.markdown("# 📋 Care Log")
    st.caption("Your plant care history, insights, and notes — all in one place.")

    plants = cached_api.get_plants()
    all_events = cached_api.get_care_events(limit=200)

    if not plants:
        st.info("No plants yet. Head to the Dashboard to add some!")
        return

    plant_map = {p["id"]: p for p in plants}
    now = datetime.now(timezone.utc)

    # -------------------------------------------------------------------
    # Section 1 — Summary stats
    # -------------------------------------------------------------------
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    this_week = sum(1 for e in all_events if (_parse_dt(e.get("created_at", "")) or datetime.min.replace(tzinfo=timezone.utc)) >= week_ago)
    this_month = sum(1 for e in all_events if (_parse_dt(e.get("created_at", "")) or datetime.min.replace(tzinfo=timezone.utc)) >= month_ago)

    water_counts: Counter = Counter()
    for e in all_events:
        if e.get("event_type") == "watered":
            water_counts[e["plant_id"]] += 1

    streak = _compute_streak(all_events)

    most_pampered = "—"
    if water_counts:
        top_id = water_counts.most_common(1)[0][0]
        most_pampered = plant_map.get(top_id, {}).get("name", "—")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("This Week", this_week, help="Care actions in the last 7 days")
    m2.metric("This Month", this_month, help="Care actions in the last 30 days")
    m3.metric("Streak", f"{streak} day{'s' if streak != 1 else ''}")
    m4.metric("Most Pampered", most_pampered)

    st.divider()

    # -------------------------------------------------------------------
    # Section 2 — Activity timeline
    # -------------------------------------------------------------------
    st.markdown("### Activity Timeline")

    fc1, fc2 = st.columns(2)
    with fc1:
        plant_names = ["All Plants"] + sorted(p["name"] for p in plants)
        selected_plant = st.selectbox("Filter by plant", plant_names, key="tl_plant")
    with fc2:
        type_options = ["All Types"] + list(EVENT_LABELS.keys())
        selected_type = st.selectbox("Filter by event type", type_options, key="tl_type")

    filtered = all_events
    if selected_plant != "All Plants":
        pid = next((p["id"] for p in plants if p["name"] == selected_plant), None)
        if pid is not None:
            filtered = [e for e in filtered if e["plant_id"] == pid]
    if selected_type != "All Types":
        filtered = [e for e in filtered if e["event_type"] == selected_type]

    if not filtered:
        st.info("No events match your filters.")
    else:
        # Group events by day
        grouped: defaultdict[str, list] = defaultdict(list)
        for e in filtered:
            dt = _parse_dt(e.get("created_at", ""))
            grouped[_day_label(dt) if dt else "Unknown"].append((dt, e))

        for day_label, items in grouped.items():
            st.markdown(f"**{day_label}**")
            items.sort(key=lambda x: x[0] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

            for dt, e in items:
                icon = EVENT_ICONS.get(e["event_type"], "📌")
                label = EVENT_LABELS.get(e["event_type"], e["event_type"])
                pname = e.get("plant_name") or plant_map.get(e["plant_id"], {}).get("name", "?")
                detail = f" — {e['detail']}" if e.get("detail") else ""
                time_str = dt.strftime("%H:%M") if dt else ""

                with st.container(border=True):
                    c1, c2 = st.columns([1, 5])
                    with c1:
                        st.markdown(f"### {icon}")
                    with c2:
                        st.markdown(f"**{pname}** · {label}{detail}")
                        st.caption(time_str)

    st.divider()

    # -------------------------------------------------------------------
    # Section 3 — Per-plant drilldown
    # -------------------------------------------------------------------
    st.markdown("### Plant Drilldown")

    plant_choice = st.selectbox("Select a plant", [p["name"] for p in plants], key="dd_plant")
    chosen = next((p for p in plants if p["name"] == plant_choice), None)
    if not chosen:
        return

    plant_events = [e for e in all_events if e["plant_id"] == chosen["id"]]
    water_events = [e for e in plant_events if e["event_type"] == "watered"]

    freq_hours = chosen.get("water_frequency_hours", 168)
    consistency_text, consistency_help = _consistency_label(water_events, freq_hours)

    last_water_dt = None
    if water_events:
        last_water_dt = max(
            (_parse_dt(e["created_at"]) for e in water_events if _parse_dt(e["created_at"])),
            default=None,
        )
    last_text = _relative_time(last_water_dt) if last_water_dt else "Never"

    s1, s2, s3 = st.columns(3)
    s1.metric("Total Waterings", len(water_events))
    s2.metric("Consistency", consistency_text, help=consistency_help)
    s3.metric("Last Watered", last_text)

    # Full history for this plant
    if plant_events:
        st.markdown("#### History")
        for e in plant_events:
            dt = _parse_dt(e.get("created_at", ""))
            icon = EVENT_ICONS.get(e["event_type"], "📌")
            label = EVENT_LABELS.get(e["event_type"], e["event_type"])
            detail = f" — {e['detail']}" if e.get("detail") else ""
            time_str = dt.strftime("%Y-%m-%d %H:%M") if dt else ""
            st.markdown(f"{icon} **{label}**{detail}  \n`{time_str}`")
    else:
        st.info("No care events recorded for this plant yet.")

    st.divider()

    # -------------------------------------------------------------------
    # Add a care note
    # -------------------------------------------------------------------
    st.markdown("#### Add a Care Note")
    note_text = st.text_area(
        "Note",
        placeholder="e.g. Repotted into larger pot, noticed yellowing leaves...",
        key="care_note_input",
        max_chars=300,
    )
    if st.button("Save Note", type="primary", key="save_care_note"):
        if not note_text.strip():
            st.warning("Please enter a note first.")
        else:
            try:
                plant_api.create_care_event({
                    "plant_id": chosen["id"],
                    "event_type": "note",
                    "detail": note_text.strip(),
                })
                cached_api.clear_cache()
                st.success("Note saved!")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to save note: {exc}")
