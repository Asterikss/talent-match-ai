import httpx
import streamlit as st

from api.client import confirm_assignment, find_matches, get_rfps
from utils.utils import set_backgroud

if "matching_rfp" not in st.session_state:
  st.session_state.matching_rfp = None
if "match_results" not in st.session_state:
  st.session_state.match_results = None
if "selected_programmers" not in st.session_state:
  st.session_state.selected_programmers = set()
if "assignment_success" not in st.session_state:
  st.session_state.assignment_success = None


def reset_matching_state():
  st.session_state.matching_rfp = None
  st.session_state.match_results = None
  st.session_state.selected_programmers = set()
  st.session_state.assignment_success = None


def render():
  set_backgroud()
  st.title("🎯 Match Programmers to RFP")

  if st.session_state.assignment_success:
    render_success()
    return

  if st.session_state.matching_rfp is None:
    render_rfp_selection()
  else:
    render_matching_interface()


def render_success():
  """Show success message after assignment."""
  result = st.session_state.assignment_success

  st.success("✅ Project Created Successfully!")

  st.markdown(f"""
    ### Assignment Complete

    - **New Project ID:** `{result.get("project_id", "N/A")}`
    - **From RFP:** `{result.get("rfp_id", "N/A")}`
    """)

  if st.button("← Start New Match", type="primary"):
    reset_matching_state()
    st.rerun()


def render_rfp_selection():
  """Show list of RFPs to select from."""
  st.markdown("Select an RFP to find matching programmers.")

  try:
    rfps = get_rfps()
  except httpx.HTTPStatusError as e:
    st.error(f"API Error: {e.response.status_code}")
    return
  except httpx.RequestError as e:
    st.error(f"Connection error: {e}")
    return

  if not rfps:
    st.info("No RFPs available. Import some RFPs first.")
    return

  for rfp in rfps:
    render_rfp_card(rfp)


def render_rfp_card(rfp: dict, find_matches_action: bool = True, boarder: bool = True):
  """Render a single RFP card with match button."""
  with st.container(border=boarder):
    col1, col2 = st.columns([4, 1])

    with col1:
      title = rfp.get("title") or rfp["id"]
      st.markdown(f"### {title}")

      info_parts = []
      if rfp.get("client"):
        info_parts.append(f"**Client:** {rfp['client']}")
      if rfp.get("budget"):
        info_parts.append(f"**Budget:** {rfp['budget']}")

      if info_parts:
        st.markdown(" • ".join(info_parts))

      skills = rfp.get("needed_skills", [])
      if skills:
        mandatory = [s["name"] for s in skills if s.get("mandatory")]
        optional = [s["name"] for s in skills if not s.get("mandatory")]

        if mandatory:
          st.markdown(f"🔴 **Required:** {', '.join(mandatory)}")
        if optional:
          st.markdown(
            f"⚪ **Optional:** {', '.join(optional[:5])}"
            + (f" (+{len(optional) - 5} more)" if len(optional) > 5 else "")
          )

    if find_matches_action:
      with col2:
        st.markdown("")
        if st.button(
          "Find Matches",
          key=f"match_{rfp['id']}",
          type="primary",
          use_container_width=True,
        ):
          st.session_state.matching_rfp = rfp
          st.session_state.match_results = None
          st.session_state.selected_programmers = set()
          st.rerun()


def render_matching_interface():
  """Main matching interface after RFP is selected."""
  rfp = st.session_state.matching_rfp

  col1, col2 = st.columns([1, 5])
  with col1:
    if st.button("← Back"):
      reset_matching_state()
      st.rerun()
  with col2:
    st.markdown(f"## Matching for: {rfp.get('title') or rfp['id']}")

  with st.expander("📋 RFP Details", expanded=False):
    render_rfp_card(rfp, find_matches_action=False, boarder=False)

  st.markdown("---")

  col1, col2 = st.columns([3, 1])
  with col1:
    threshold = st.slider(
      "Consider programmers available within (months):",
      min_value=1,
      max_value=12,
      value=1,
      help="Programmers becoming available within this period will be shown as 'Available Soon'",
    )
  with col2:
    if st.button("🔄 Refresh Matches", use_container_width=True):
      st.session_state.match_results = None

  if st.session_state.match_results is None:
    with st.spinner("Finding matching programmers..."):
      try:
        results = find_matches(rfp["id"], threshold)
        st.session_state.match_results = results
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

  results = st.session_state.match_results
  render_match_results(results)

  st.markdown("---")
  render_confirmation_section(rfp)


def render_match_results(results: dict):
  """Render the three categories of matches."""
  perfect = results.get("perfect_matches", [])
  future = results.get("future_matches", [])
  partial = results.get("partial_matches", [])

  total = len(perfect) + len(future) + len(partial)

  if total == 0:
    st.warning("No matching programmers found for this RFP.")
    return

  st.markdown(f"### Found {total} potential candidate{'s' if total > 1 else ''}")

  if perfect:
    st.markdown("#### 🧩 Perfect Matches")
    st.caption("Available now • All mandatory skills met")
    for candidate in perfect:
      render_candidate_card(candidate)

  if future:
    st.markdown("#### 🌘 Available Soon")
    st.caption("All mandatory skills met • Currently assigned")
    for candidate in future:
      render_candidate_card(candidate)

  if partial:
    st.markdown("#### 🌓 Partial Matches")
    st.caption("Available now • Missing mandatory skills")
    for candidate in partial:
      if candidate["status"] != "unavailable":
        render_candidate_card(candidate)


def render_candidate_card(candidate: dict):
  """Render a single candidate with selection checkbox."""
  programmer_id = candidate["programmer_id"]
  is_selected = programmer_id in st.session_state.selected_programmers

  with st.container(border=True):
    col_check, col_info, col_stats = st.columns([0.5, 3, 2])

    with col_check:
      selected = st.checkbox(
        "Select",
        value=is_selected,
        key=f"select_{programmer_id}",
        label_visibility="collapsed",
      )
      if selected:
        st.session_state.selected_programmers.add(programmer_id)
      else:
        st.session_state.selected_programmers.discard(programmer_id)

    with col_info:
      name = candidate.get("programmer_name") or programmer_id
      role = candidate.get("role") or "Developer"
      total_score = candidate.get("total_score", 0)

      st.markdown(f"**{name}**")
      st.caption(f"{role} • Score: {total_score:.0f}")

      missing_mandatory = candidate.get("missing_mandatory_skills", [])
      if missing_mandatory:
        st.markdown(f"🌓 **Missing mandatory:** {', '.join(missing_mandatory)}")

      missing_optional = candidate.get("missing_optional_skills", [])
      if missing_optional:
        st.caption(f"Missing optional: {', '.join(missing_optional)}")

    with col_stats:
      skill_pct = candidate.get("skill_match_percent", 0)

      st.progress(
        skill_pct / 100,
        text=f"Skill Match: {skill_pct:.0f}%",
      )

      status = candidate.get("status")
      days = candidate.get("days_until_available", 0)
      end_date = candidate.get("current_project_end_date")
      project = candidate.get("current_project_name")

      if status == "available":
        st.markdown("🟢 Available now")

      elif status == "available_soon":
        st.markdown(f"🟡 Available in {days} days")
        if project:
          st.caption(f"📁 {project}")
        elif end_date:
          st.caption(f"Project ends: {end_date}")

      else:
        st.markdown(f"🔴 Unavailable ({days} days)")


def render_confirmation_section(rfp: dict):
  """Render the final confirmation section."""
  selected = st.session_state.selected_programmers

  if not selected:
    st.info("Select programmers above to assign them to this project.")
    return

  st.markdown(f"### 📝 Assignment Summary")
  st.markdown(f"**Selected {len(selected)} programmer(s):**")

  results = st.session_state.match_results
  all_candidates = (
    results.get("perfect_matches", [])
    + results.get("future_matches", [])
    + results.get("partial_matches", [])
  )
  selected_names = [
    c.get("programmer_name", c["programmer_id"])
    for c in all_candidates
    if c["programmer_id"] in selected
  ]

  for name in selected_names:
    st.markdown(f"- {name}")

  st.warning(
    "⚠︎ This will convert the RFP into a Project and assign the selected "
    "programmers. The RFP will no longer be available for matching."
  )

  col1, col2 = st.columns([1, 1])
  with col1:
    if st.button("Cancel", use_container_width=True):
      reset_matching_state()
      st.rerun()
  with col2:
    if st.button("Confirm Assignment", type="primary", use_container_width=True):
      with st.spinner("Creating project and assigning programmers..."):
        try:
          result = confirm_assignment(rfp["id"], list(selected))
          st.session_state.assignment_success = result
          st.rerun()
        except httpx.HTTPStatusError as e:
          st.error(f"API Error: {e.response.status_code}")
          try:
            detail = e.response.json().get("detail", str(e))
          except Exception:
            detail = e.response.text
          st.code(detail)
        except httpx.RequestError as e:
          st.error(f"Connection error: {e}")


render()
