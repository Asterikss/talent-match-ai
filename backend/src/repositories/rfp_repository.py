from src.core.models import RFPRead
from src.services.neo4j_service import get_neo4j_graph


def get_rfps() -> list[RFPRead]:
  """
  Fetches RFPs with needed skills.
  """
  cypher = """
    MATCH (r:RFP)

    OPTIONAL MATCH (r)-[rel:NEEDS]->(s:Skill)

    WITH r, collect({
      name: s.id,
      level: rel.experience_level,
      mandatory: rel.mandatory
      }) as skills

    RETURN {
      id: r.id,
      title: r.title,
      client: r.client,
      budget: r.budget,
      needed_skills: skills
      } as data
    ORDER BY r.id
  """

  results = get_neo4j_graph().query(cypher)
  return [RFPRead(**row["data"]) for row in results]


def get_next_rfp_id() -> str:
  """Get the next available RFP ID from Neo4j."""
  graph = get_neo4j_graph()
  result = graph.query("""
        MATCH (r:RFP)
        RETURN r.id AS id
        ORDER BY r.id DESC
        LIMIT 1
    """)
  if not result:
    return "RFP-001"

  last_id = result[0]["id"]  # e.g., "RFP-042"
  num = int(last_id.split("-")[1]) + 1
  return f"RFP-{num:03d}"
