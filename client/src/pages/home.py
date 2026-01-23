import streamlit as st

from utils.utils import set_backgroud


def render():
  set_backgroud()
  st.title("🎯 Talent Match AI")
  st.markdown("---")

  st.markdown("""
    Welcome to **Talent Match AI** — your intelligent platform for matching
    programmers with projects and RFPs.

    ### What you can do here:

    - 💻 **Programmers** — View and manage your talent pool
    - 📁 **Projects** — Track active and completed projects
    - 📋 **RFPs** — Browse incoming requests for proposals

    ### How it works

    This platform uses a **Neo4j graph database** to model relationships between 
    programmers, their skills, projects, and RFPs. This allows for intelligent 
    matching based on skill requirements, availability, and project needs.

    ---

    Use the sidebar navigation to get started.
  """)

  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric("Platform", "Neo4j + FastAPI")
  with col2:
    st.metric("Matching", "Graph-based")
  with col3:
    st.metric("Status", "🟢 Online")


render()
