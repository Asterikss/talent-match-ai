import streamlit as st

from api.client import get_programmers
from utils.utils import set_backgroud


def render():
  set_backgroud()
  st.title("👨💻 Programmers")

  status_filter = st.selectbox(
    "Filter by status",
    options=[None, "available", "assigned"],
    format_func=lambda x: "All" if x is None else x.capitalize(),
  )

  try:
    programmers = get_programmers(status_filter)
  except Exception as e:
    st.error(f"Failed to fetch programmers: {e}")
    return

  if not programmers:
    st.info("No programmers found.")
    return

  st.markdown(f"**{len(programmers)}** programmer(s) found")

  for prog in programmers:
    with st.container(border=True):
      col1, col2 = st.columns([3, 1])

      with col1:
        st.subheader(prog["id"])
        if prog["skills"]:
          skills_str = ", ".join(prog["skills"][:8])
          if len(prog["skills"]) > 8:
            skills_str += f" (+{len(prog['skills']) - 8} more)"
          st.caption(f"**Skills:** {skills_str}")

      with col2:
        if prog["is_assigned"]:
          st.success("Assigned")
          if prog["current_project"]:
            st.caption(f"📁 {prog['current_project']}")
        else:
          st.warning("Available")


render()
