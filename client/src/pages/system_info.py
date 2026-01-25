import httpx
import streamlit as st

from api.client import get_graph_stats, get_node_sample
from utils.utils import set_backgroud


def render():
  set_backgroud()
  st.title("📊 System Info")

  tab_stats, tab_sample = st.tabs(["Graph Statistics", "Node Samples"])

  with tab_stats:
    render_stats()

  with tab_sample:
    render_samples()


def render_stats():
  if st.button("🔄 Refresh", key="refresh_stats"):
    st.rerun()

  with st.spinner("Fetching statistics..."):
    try:
      stats = get_graph_stats()
    except httpx.HTTPStatusError as e:
      st.error(f"API Error: {e.response.status_code}")
      try:
        detail = e.response.json().get("detail", str(e))
      except Exception:
        detail = e.response.text
      st.code(detail)
      return
    except httpx.RequestError as e:
      st.error(f"Connection error: {e}")
      return

  if not stats:
    st.info("No statistics available.")
    return

  status = stats.get("status", "unknown")
  if status == "healthy":
    st.success("✅ Graph Status: Healthy")
  else:
    st.warning(f"⚠️ Graph Status: {status}")

  warnings = stats.get("warnings", [])
  if warnings:
    for w in warnings:
      st.warning(w)

  summary = stats.get("summary", {})
  if summary:
    col1, col2 = st.columns(2)
    with col1:
      st.metric("Total Nodes", summary.get("total_nodes", 0))
    with col2:
      st.metric("Total Relationships", summary.get("total_relationships", 0))

  schema = stats.get("schema", {})
  if schema:
    st.markdown("---")
    col_nodes, col_rels = st.columns(2)

    with col_nodes:
      st.markdown("### Node Labels")
      nodes = schema.get("nodes", {})
      if nodes:
        for label, count in sorted(nodes.items(), key=lambda x: -x[1]):
          st.markdown(f"- **{label}**: {count}")
      else:
        st.caption("No nodes found")

    with col_rels:
      st.markdown("### Relationship Types")
      rels = schema.get("relationships", {})
      if rels:
        for rel_type, count in sorted(rels.items(), key=lambda x: -x[1]):
          st.markdown(f"- **{rel_type}**: {count}")
      else:
        st.caption("No relationships found")

  domain_stats = stats.get("domain_stats", {})
  if domain_stats:
    st.markdown("---")
    st.markdown("### Domain Statistics")
    for pattern, count in domain_stats.items():
      st.markdown(f"- `{pattern}`: {count}")

  with st.expander("📄 Raw Response"):
    st.json(stats)


def render_samples():
  st.markdown("View sample records for a specific node type to inspect data quality.")

  common_labels = ["Person", "Project", "RFP", "Skill", "Company"]

  label = st.selectbox(
    "Select Node Label",
    options=common_labels,
    index=0,
    help="Select a node label to fetch samples",
  )

  custom_label = st.text_input(
    "Or enter custom label",
    placeholder="e.g., Certification",
  )

  selected_label = custom_label.strip() if custom_label.strip() else label

  if st.button("Fetch Samples", type="primary"):
    with st.spinner(f"Fetching samples for '{selected_label}'..."):
      try:
        samples = get_node_sample(selected_label)
      except httpx.HTTPStatusError as e:
        st.error(f"API Error: {e.response.status_code}")
        try:
          detail = e.response.json().get("detail", str(e))
        except Exception:
          detail = e.response.text
        st.code(detail)
        return
      except httpx.RequestError as e:
        st.error(f"Connection error: {e}")
        return

      if not samples:
        st.warning(f"No samples found for label '{selected_label}'.")
        return

      st.success(f"Found {len(samples)} sample(s)")

      for i, sample in enumerate(samples):
        with st.expander(f"Sample {i + 1}", expanded=(i == 0)):
          st.json(sample)


render()
