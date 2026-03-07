"""
Streamlit main entrypoint for the Pramaan frontend.

Streamlit will automatically discover additional pages from the `pages/` directory.
Run with:
    streamlit run frontend/app.py
from the project root.
"""

import streamlit as st


def main() -> None:
    st.set_page_config(page_title="Pramaan", layout="wide")
    st.title("Pramaan")
    st.write(
        "Welcome to the Pramaan prototype. Use the sidebar to navigate between pages."
    )


if __name__ == "__main__":
    main()

