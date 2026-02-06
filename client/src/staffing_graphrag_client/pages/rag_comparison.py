import streamlit as st

from utils.utils import set_backgroud


def render():
  set_backgroud()
  st.title("📋 GraphRAG vs Naive RAG Evaluation Results")
  st.caption("Comparison of performance across evaluation questions.")

  table_data = {
    "Question": [
      "How many people are in the knowledge graph?",
      "Who has both Docker and Kubernetes skills?",
      "Find people who worked at the same companies.",
      "Find people who are currently assigned to the same project.",
      "Who has cloud computing skills like AWS?",
      "What programming languages are most common?",
      "What companies have the most former employees in our database?",
      "List all companies mentioned in the CVs.",
      "Find people who studied at Ivy League schools.",
      "What universities are most common in our database?",
      "Find people that studied at the same university.",
      "What cities have the most people?",
      "Who is located in Deniseborough?",
      "Show all locations in our database.",
      "Who has AWS certifications?",
      "Find all Google Cloud certified people.",
      "What are the most common certifications?",
    ],
    "GraphRAG": [
      "🟢",
      "🟢",
      "🟢",
      "🟢",
      "🟢",
      "🟢",
      "🟢",
      "🟢",
      "🟢",
      "🟢",
      "🔴",
      "🟢",
      "🟢",
      "🟢",
      "🟡*",
      "🟡*",
      "🟢",
    ],
    "Naive RAG": [
      "🔴",
      "🟢",
      "🔴",
      "🔴",
      "🟢",
      "🔴",
      "🟢",
      "🔴",
      "🔴",
      "🔴",
      "🔴",
      "🔴",
      "🟢",
      "🔴",
      "🔴",
      "🔴",
      "🟢",
    ],
  }

  st.table(table_data, border="horizontal")

  st.caption(
    "*Partial success: A slight prompt change was required to achieve the expected result."
  )


render()
