import logging

from core.models.models import CandidateMatch, MatchResponse
from services.neo4j_service import get_neo4j_graph

logger = logging.getLogger(__name__)


class MatchingRepository:
  def __init__(self):
    self.graph = get_neo4j_graph()

  def find_candidates(self, rfp_id: str, max_delay_months: int = 1) -> MatchResponse:
    """
    Finds candidates by matching RFP Needs -> Skill <- Person Has Skill.
    Fixes:
    1. Correctly collects Skill IDs from the NEEDS relationship.
    2. Uses COALESCE for date handling (deadline vs start_date).
    """

    query = """
        MATCH (r:RFP {id: $rfp_id})
        MATCH (p:Person)

        // --- 1. SKILL SCORING ---
        // We match the RFP to the Skills it needs
        OPTIONAL MATCH (r)-[req:NEEDS]->(s:Skill)

        // CRITICAL FIX: Collect a map containing the Node ID and the Edge properties
        WITH r, p, collect({id: s.id, mandatory: req.mandatory}) as requirements

        // Check which of these specific skills the Person has
        OPTIONAL MATCH (p)-[:HAS_SKILL]->(ps:Skill)
        WHERE ps.id IN [x IN requirements | x.id]

        WITH r, p, requirements, collect(ps.id) as person_skills

        // Calculate Score
        // Iterate over requirements map we built earlier
        WITH r, p, requirements, person_skills,
             reduce(score = 0, item IN requirements |
                score + CASE
                    WHEN item.id IN person_skills THEN 
                        CASE WHEN item.mandatory THEN 10 ELSE 5 END 
                    ELSE 0
                END
             ) as total_score,
             [item IN requirements WHERE item.mandatory AND NOT item.id IN person_skills | item.id] as missing_mandatory,
             size(requirements) as total_reqs,
             size(person_skills) as matched_count

        WHERE total_score > 0

        // --- 2. AVAILABILITY CALCULATION ---
        OPTIONAL MATCH (p)-[assign:ASSIGNED_TO]->(proj:Project)
        WHERE proj.status IN ['active', 'planned']

        WITH r, p, total_score, missing_mandatory, total_reqs, matched_count,
             max(date(assign.end_date)) as last_project_end,
             // Handle inconsistent date property naming (deadline vs start_date)
             coalesce(date(r.start_date), date(r.deadline)) as rfp_start

        WITH r, p, total_score, missing_mandatory, total_reqs, matched_count, last_project_end, rfp_start,
             CASE
                WHEN last_project_end IS NULL THEN -999
                ELSE duration.inDays(rfp_start, last_project_end).days 
             END as delay_days

        RETURN {
            id: p.id,
            name: coalesce(p.name, p.id),
            role: coalesce(p.level, p.role, 'Developer'),
            total_score: total_score,
            skill_match_percent: CASE WHEN total_reqs = 0 THEN 0 ELSE (toFloat(matched_count) / toFloat(total_reqs)) * 100 END,
            missing_mandatory: missing_mandatory,
            delay_days: delay_days,
            last_end_date: toString(last_project_end)
        } as candidate
        ORDER BY total_score DESC
        """

    results = self.graph.query(query, params={"rfp_id": rfp_id})

    response = MatchResponse(rfp_id=rfp_id)

    for row in results:
      data = row["candidate"]
      delay = data["delay_days"]

      # Categorize
      if delay <= 0:
        status = "available"
      elif delay <= (max_delay_months * 30):
        status = "available_soon"
      else:
        status = "unavailable"

      candidate = CandidateMatch(
        programmer_id=str(data["id"]),
        programmer_name=data["name"],
        role=data.get("role"),
        total_score=data["total_score"],
        skill_match_percent=round(data["skill_match_percent"], 1),
        missing_mandatory_skills=data["missing_mandatory"],
        status=status,
        days_until_available=delay if delay > 0 else 0,
        current_project_end_date=data["last_end_date"],
      )

      if len(candidate.missing_mandatory_skills) > 0:
        response.partial_matches.append(candidate)
      elif status == "available":
        response.perfect_matches.append(candidate)
      elif status == "available_soon":
        response.future_matches.append(candidate)

    return response

  def convert_rfp_to_project(self, rfp_id: str, programmer_ids: list[str]):
    """
    Transactional logic to:
    1. Create Project from RFP
    2. Assign Programmers
    3. Delete RFP
    """

    cypher = """
        MATCH (r:RFP {id: $rfp_id})

        // 1. Create Project Node
        CREATE (p:Project {
            id: 'PROJ-' + r.id,  // Generate a new ID TODO
            title: r.title,
            description: r.description,
            client: r.client,
            budget: r.budget,
            start_date: r.start_date,
            // Calculate end date approximately
            end_date: toString(date(r.start_date) + duration({months: coalesce(r.duration_months, 6)})),
            status: 'active',
            team_size: r.team_size
        })

        // 2. Copy Requirements (RFP)-[:NEEDS]->(Skill) ==> (Project)-[:REQUIRES]->(Skill)
        WITH r, p
        MATCH (r)-[needs:NEEDS]->(s:Skill)
        CREATE (p)-[req:REQUIRES]->(s)
        SET req.minimum_level = needs.experience_level,
            req.mandatory = needs.mandatory

        // 3. Assign Selected Programmers
        WITH r, p
        MATCH (u:Person)
        WHERE u.id IN $programmer_ids OR toInteger(u.id) IN $programmer_ids

        CREATE (u)-[assign:ASSIGNED_TO]->(p)
        SET assign.start_date = p.start_date,
            assign.end_date = p.end_date,
            assign.allocation_percentage = 100

        // 4. Delete the RFP
        DETACH DELETE r

        RETURN p.id as new_project_id
        """

    result = self.graph.query(
      cypher, params={"rfp_id": rfp_id, "programmer_ids": programmer_ids}
    )

    if not result:
      raise ValueError(f"Failed to convert RFP {rfp_id}. It might not exist.")

    return result[0]["new_project_id"]
