import streamlit as st

import plant_api


@st.cache_data(ttl=2, show_spinner=False)
def get_plants():
    return plant_api.get_plants()


def clear_cache():
    get_plants.clear()
