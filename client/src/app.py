import streamlit as st

st.set_page_config(
  page_title="Talent Match AI",
  page_icon="🎯",
  layout="wide",
)

home = st.Page("pages/home.py", title="Home", icon=":material/home:", default=True)

query = st.Page("pages/query.py", title="Query", icon=":material/search:")

matching = st.Page("pages/matching.py", title="Match", icon=":material/hub:")

programmers = st.Page(
  "pages/programmers.py", title="Programmers", icon=":material/person:"
)
add_programmer = st.Page(
  "pages/add_programmer.py", title="Add Programmer", icon=":material/person_add:"
)

projects = st.Page("pages/projects.py", title="Projects", icon=":material/folder:")
add_project = st.Page(
  "pages/add_project.py", title="Add Project", icon=":material/create_new_folder:"
)

rfps = st.Page("pages/rfps.py", title="RFPs", icon=":material/description:")
add_rfp = st.Page("pages/add_rfp.py", title="Ingest RFP", icon=":material/note_add:")

system_info = st.Page(
  "pages/system_info.py", title="System Info", icon=":material/monitoring:"
)
rag_comparison = st.Page(
  "pages/rag_comparison.py", title="RAG comparison", icon=":material/compare_arrows:"
)

pg = st.navigation(
  {
    "Home": [home],
    "Query": [query],
    "Matching": [matching],
    "Programmers": [programmers, add_programmer],
    "RFPs": [rfps, add_rfp],
    "Projects": [projects, add_project],
    "System": [system_info, rag_comparison],
  }
)

pg.run()
