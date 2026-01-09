import logging

from core.models import CandidateMatch, MatchResponse
from services.neo4j_service import get_neo4j_graph

logger = logging.getLogger(__name__)


class MatchingRepository:
  def __init__(self):
    self.graph = get_neo4j_graph()

  def find_candidates(self, rfp_id: str, max_delay_months: int = 1) -> MatchResponse:
    """
    complex matching algorithm:
    1. Scores skills (Mandatory = 10pts, Optional = 5pts).
    2. Calculates availability based on current active assignments.
    3. Returns categorized candidates.
    """

    # Cypher logic:
    # 1. Find RFP and its required skills.
    # 2. Match against all Persons.
    # 3. Calculate Skill Score & Check Mandatories.
    # 4. Check 'ASSIGNED_TO' relations where project is active.
    # 5. Calculate gap between RFP.start_date and max(Assignment.end_date).

    query = """
        MATCH (r:RFP {id: $rfp_id})
        MATCH (p:Person)

        // --- 1. SKILL SCORING ---
        // Find skills the RFP needs
        OPTIONAL MATCH (r)-[req:NEEDS]->(s:Skill)
        WITH r, p, collect(req) as requirements

        // Find skills the Person has intersecting with Requirements
        OPTIONAL MATCH (p)-[:HAS_SKILL]->(ps:Skill)
        WHERE ps.id IN [x IN requirements | x.id] // Only care about relevant skills
        WITH r, p, requirements, collect(ps.id) as person_skills

        // Calculate Score
        // iterate over requirements, check if person has it
        WITH r, p, requirements, person_skills,
             [req IN requirements |
                CASE WHEN req.name IN person_skills THEN
                    CASE WHEN req.mandatory THEN 10 ELSE 5 END
                ELSE 0 END
             ] as scores,
             [req IN requirements WHERE req.mandatory AND NOT req.name IN person_skills | req.name] as missing_mandatory

        WITH r, p, person_skills, missing_mandatory,
             reduce(total = 0, s IN scores | total + s) as total_score,
             size(requirements) as total_reqs,
             size(person_skills) as matched_count

        WHERE total_score > 0 // Filter out completely unqualified people

        // --- 2. AVAILABILITY CALCULATION ---
        // Find active projects the person is working on
        OPTIONAL MATCH (p)-[assign:ASSIGNED_TO]->(proj:Project)
        WHERE proj.status IN ['active', 'planned']

        WITH r, p, total_score, missing_mandatory, total_reqs, matched_count,
             max(date(assign.end_date)) as last_project_end,
             date(r.start_date) as rfp_start

        // Calculate availability gap in days
        // If last_project_end is null, they are free (gap = -999)
        // If rfp_start > last_project_end, they are free (gap = negative)
        // If rfp_start < last_project_end, they are busy (gap = positive days overlap)

        // WITH r, p, totalScore, missingMandatory, requirements, personSkills,
        WITH r, p, total_score, missing_mandatory, total_reqs, matched_count, last_project_end, rfp_start,
             CASE
                WHEN last_project_end IS NULL THEN -999
                ELSE duration.inDays(rfp_start, last_project_end).days
             END as delay_days

        // role: p.level,
        RETURN {
            id: p.id,
            name: p.name,
            total_score: total_score,
            skill_match_percent: (toFloat(matched_count) / toFloat(total_reqs)) * 100,
            missing_mandatory: missing_mandatory,
            delay_days: delay_days,
            last_end_date: toString(last_project_end)
        } as candidate
        ORDER BY total_score DESC
        """

    results = self.graph.query(query, params={"rfp_id": rfp_id})
    print("here")
    print(results)
    print("here2")

    response = MatchResponse(rfp_id=rfp_id)

    for row in results:
      data = row["candidate"]
      # delay = data["delay_days"]
      delay = data["delay_days"] if data["delay_days"] is not None else -999

      # Categorize
      if delay <= 0:
        status = "available"
      elif delay <= (max_delay_months * 30):
        status = "available_soon"
      else:
        status = "unavailable"

      candidate = CandidateMatch(
        programmer_id=str(data["id"]),  # Cast to str just in case
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
    # We assume the RFP start_date is the project start_date
    # We calculate end_date based on duration_months

    cypher = """
        MATCH (r:RFP {id: $rfp_id})

        // 1. Create Project Node
        CREATE (p:Project {
            id: 'PROJ-' + r.id,  // Generate a new ID
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
