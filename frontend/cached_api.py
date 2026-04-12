"""Thin caching layer over ``plant_api``.

Streamlit re-runs the entire script on every interaction.  These
wrappers use ``@st.cache_data`` with a short TTL (2 s) so repeated
renders within the same interaction don't hammer the backend.  After
any write operation (create / update / delete / water), call
``clear_cache()`` to force a fresh fetch on the next rerun.
"""

import streamlit as st

import plant_api


@st.cache_data(ttl=2, show_spinner=False)
def get_plants():
    return plant_api.get_plants()


@st.cache_data(ttl=2, show_spinner=False)
def get_care_events(plant_id=None, event_type=None, limit=50):
    return plant_api.get_care_events(
        plant_id=plant_id, event_type=event_type, limit=limit
    )


def clear_cache():
    """Invalidate all cached API responses so the next call fetches fresh data."""
    get_plants.clear()
    get_care_events.clear()
