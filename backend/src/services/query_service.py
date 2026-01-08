import logging
from typing import Any

from langchain_neo4j import GraphCypherQAChain

from core import constants, prompts
from services.neo4j_service import get_neo4j_graph
from services.openai_service import get_openai_chat

logger = logging.getLogger(__name__)


def get_qa_chain() -> GraphCypherQAChain:
  """
  Initializes the GraphCypherQAChain.
  This creates the link between the LLM and the Neo4j database.
  """
  graph = get_neo4j_graph()

  openai_chat_resulta = get_openai_chat(constants.OPENAI_QUERY_MODEL)
  if openai_chat_resulta.err():
    raise  # TODO: propagate further

  return GraphCypherQAChain.from_llm(
    llm=openai_chat_resulta.ok(),
    graph=graph,
    verbose=True,
    cypher_prompt=prompts.cypher_generation_prompt,
    qa_prompt=prompts.cypher_qa_prompt,
    return_intermediate_steps=True,
    allow_dangerous_requests=True,  # Required for chains that can execute DB queries
    validate_cypher=True,
  )


async def process_query(question: str) -> dict[str, Any]:
  """
  Executes a natural language query against the Knowledge Graph.
  """
  try:
    chain = get_qa_chain()

    result: dict[str, Any] = await chain.ainvoke({"query": question})

    # Extract intermediate step (the actual Cypher query generated)
    # intermediate_steps is a list of dicts or tuples depending on chain version
    cypher_query = ""
    steps = result.get("intermediate_steps", [])
    if steps and isinstance(steps[0], dict):
      cypher_query = steps[0].get("query", "")

    return {
      "question": question,
      "answer": result.get("result", "No answer generated"),
      "cypher_query": cypher_query,
      "success": True,
    }

  except Exception as e:
    logger.error(f"Graph QA failed: {e}")
    return {
      "question": question,
      "answer": "I encountered an error processing your query.",
      "error": str(e),
      "success": False,
    }


def get_example_queries_list() -> dict[str, list[str]]:
  """
  Returns a categorized list of example queries for the frontend.
  """
  return {
    "Basic Information": [
      "How many people are in the knowledge graph?",
      "What companies appear in the CVs?",
      "List all the skills mentioned in the CVs.",
      "What certifications do people have?",
      "Which universities appear in the CVs?",
      "What job titles are mentioned?",
      "Show me all the locations where people are based.",
    ],
    "Skill-based Queries": [
      "Who has Python programming skills?",
      "Find all people with React experience.",
      "Who has both Docker and Kubernetes skills?",
      "List people with JavaScript skills.",
      "Find people who know both Python and Django.",
      "Who has cloud computing skills like AWS?",
      "What programming languages are most common?",
      "Find people with machine learning expertise.",
    ],
    "Company Experience": [
      "Who worked at Google?",
      "Find people who worked at Microsoft.",
      "What companies have the most former employees in our database?",
      "Who worked at technology companies?",
      "Find people with startup experience.",
      "List all companies mentioned in the CVs.",
      "Who has experience at Fortune 500 companies?",
    ],
    "Education Background": [
      "Who studied at Stanford University?",
      "Find people with computer science education.",
      "What universities are most common in our database?",
      "Who has a Master's degree?",
      "Find people who studied at Ivy League schools.",
      "What are the most common degree types?",
      "Who has a PhD?",
    ],
    "Location and Geography": [
      "Who is located in San Francisco?",
      "Find people in California.",
      "What cities have the most people?",
      "Who is located in New York?",
      "Find people in the United States.",
      "Show all locations in our database.",
      "Find people willing to relocate.",
    ],
    "Professional Experience": [
      "Who has the most years of experience?",
      "Find senior-level professionals.",
      "Who worked in software development roles?",
      "Find people with leadership experience.",
      "Who has experience in data science?",
      "List all job titles mentioned.",
      "Find people with consulting experience.",
    ],
    "Multi-hop Reasoning": [
      "Find people who worked at the same companies.",
      "Who went to the same university and has similar skills?",
      "Find people who have complementary skills for a team.",
      "What skills are commonly paired together?",
      "Find potential colleagues based on shared experience.",
      "Who studied at top universities and has industry experience?",
      "Find people with both technical and business skills.",
    ],
    "Certification Analysis": [
      "Who has AWS certifications?",
      "Find all Google Cloud certified people.",
      "What are the most common certifications?",
      "Who has multiple certifications?",
      "Find people with security certifications.",
      "List all certification providers.",
      "Who has recent certifications?",
    ],
  }
