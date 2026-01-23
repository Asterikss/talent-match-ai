import httpx
import streamlit as st

from api.client import get_example_queries, query_knowledge_graph
from utils.utils import set_backgroud

if "query_history" not in st.session_state:
  st.session_state.query_history = []

if "pending_query" not in st.session_state:
  st.session_state.pending_query = None


def execute_query(question: str):
  st.session_state.query_history.append({"role": "user", "content": question})

  try:
    result = query_knowledge_graph(question)
    st.session_state.query_history.append(
      {
        "role": "assistant",
        "content": result.get("answer", "No answer returned."),
        "cypher": result.get("cypher_query", ""),
        "success": result.get("success", False),
        "error": result.get("error"),
      }
    )
  except httpx.HTTPStatusError as e:
    try:
      detail = e.response.json().get("detail", str(e))
    except Exception:
      detail = e.response.text
    st.session_state.query_history.append(
      {
        "role": "assistant",
        "content": f"API Error: {e.response.status_code}",
        "error": detail,
        "success": False,
      }
    )
  except httpx.RequestError as e:
    st.session_state.query_history.append(
      {
        "role": "assistant",
        "content": "Connection error",
        "error": str(e),
        "success": False,
      }
    )


def render():
  set_backgroud()
  st.title("🔍 Query Knowledge Graph")

  with st.sidebar:
    render_examples_sidebar()

  render_chat_history()
  render_quick_examples()
  render_chat_input()


def render_examples_sidebar():
  st.markdown("### 💡 Example Queries")

  try:
    examples = get_example_queries()
  except Exception:
    st.caption("Could not load examples")
    return

  for category, queries in examples.items():
    with st.expander(category):
      for i, q in enumerate(queries):
        if st.button(q, key=f"sidebar_{i}_{q}", use_container_width=True):
          st.session_state.pending_query = q
          st.rerun()


def render_chat_history():
  if not st.session_state.query_history:
    st.markdown(
      """
      <div style="text-align: center; padding: 2rem; color: #888;">
          <p>Ask questions about your knowledge graph in natural language.</p>
          <p>Try one of the examples below or type your own question.</p>
      </div>
      """,
      unsafe_allow_html=True,
    )
    return

  for msg in st.session_state.query_history:
    with st.chat_message(msg["role"]):
      if msg["role"] == "user":
        st.markdown(msg["content"])
      else:
        if not msg.get("success"):
          st.error(msg["content"])
          st.code(msg["error"])
        else:
          st.markdown(msg["content"])

          cypher = msg.get("cypher", "")
          if cypher:
            with st.expander("🔧 Cypher Query"):
              st.code(cypher, language="cypher")


def render_quick_examples():
  if st.session_state.query_history:
    return

  try:
    examples = get_example_queries()
    basic_examples = examples.get("Basic Information", [])[:4]
  except Exception:
    basic_examples = []

  if not basic_examples:
    return

  st.markdown("**Quick examples:**")
  cols = st.columns(len(basic_examples))
  for i, example in enumerate(basic_examples):
    with cols[i]:
      if st.button(example, key=f"quick_{i}", help=example, use_container_width=True):
        st.session_state.pending_query = example
        st.rerun()


def render_chat_input():
  if st.session_state.pending_query:
    query = st.session_state.pending_query
    st.session_state.pending_query = None
    execute_query(query)
    st.rerun()

  _, col2 = st.columns([6, 1])
  with col2:
    if st.session_state.query_history:
      if st.button("Clear", use_container_width=True):
        st.session_state.query_history = []
        st.rerun()

  if prompt := st.chat_input("Ask a question about your knowledge graph..."):
    execute_query(prompt)
    st.rerun()


render()
