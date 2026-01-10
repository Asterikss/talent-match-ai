from core.models import ProgrammerRead
from services.neo4j_service import get_neo4j_graph


def get_programmers(status: str | None = None) -> list[ProgrammerRead]:
  """
  Fetches people with their skills and assignment status.
  status: 'available' | 'assigned' | None (all)
  """
  # Logic: A person is assigned if they have an ASSIGNED_TO relationship
  # to a project that is NOT completed (i.e. active, planned).

  cypher = """
    MATCH (p:Person)

    OPTIONAL MATCH (p)-[:HAS_SKILL]->(s:Skill)

    OPTIONAL MATCH (p)-[r:ASSIGNED_TO]->(proj:Project)
    WHERE proj.status IN ['active', 'planned', 'on_hold']

    WITH p, collect(distinct s.id) as skills, collect(distinct proj.title) as active_projects

    // role: p.level,
    RETURN {
      id: p.id,
      name: p.name,
      location: p.location,
      skills: skills,
      is_assigned: size(active_projects) > 0,
      current_project: head(active_projects)
      } as data
  """

  results = get_neo4j_graph().query(cypher)
  parsed_results = [ProgrammerRead(**row["data"]) for row in results]

  # Filter in Python (simpler than complex Cypher conditional returns for list filtering)
  if status == "available":
    return [p for p in parsed_results if not p.is_assigned]
  elif status == "assigned":
    return [p for p in parsed_results if p.is_assigned]

  return parsed_results
