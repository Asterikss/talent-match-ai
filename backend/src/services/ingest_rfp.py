import json
import logging
from pathlib import Path

from result import Err

from core.models import RFPStructure
from core.utils import extract_text_from_pdf
from services.neo4j_service import save_rfp_to_graph
from services.openai_service import get_openai_chat

logger = logging.getLogger(__name__)

RFP_STORAGE_DIR = Path("data/RFP")
RFP_JSON_FILE = RFP_STORAGE_DIR / "rfps.json"


async def _extract_rfp_data(text: str) -> RFPStructure:
  """
  Uses OpenAI Structured Output to parse raw text into the RFP Pydantic model.
  """
  openai_chat_result = get_openai_chat(temperature=0)
  if isinstance(openai_chat_result, Err):
    raise  # TODO: propagate

  # with_structured_output forces the LLM to return the Pydantic object
  structured_llm = openai_chat_result.ok().with_structured_output(RFPStructure)

  try:
    result = await structured_llm.ainvoke(
      f"Extract the following RFP information from the text provided. "
      f"Infer missing dates or details logically if implied.\n\nText:\n{text}"
    )
    return result
  except Exception as e:
    logger.error(f"LLM Extraction failed: {e}")
    raise ValueError("Failed to parse RFP structure from text")


def _save_to_json_file(rfp_data: RFPStructure):
  """
  Appends the new RFP to the global rfps.json file.
  Handles creation if file doesn't exist.
  """
  # Ensure directory exists
  if not RFP_STORAGE_DIR.exists():
    RFP_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

  current_data = []

  # Load existing
  if RFP_JSON_FILE.exists():
    try:
      with open(RFP_JSON_FILE, "r") as f:
        current_data = json.load(f)
    except json.JSONDecodeError:
      logger.warning("rfps.json was corrupted, starting fresh.")
      current_data = []

  # Check for duplicates (update if exists, otherwise append)
  rfp_dict = rfp_data.model_dump()

  updated = False
  for i, item in enumerate(current_data):
    if item.get("id") == rfp_dict["id"]:
      current_data[i] = rfp_dict
      updated = True
      break

  if not updated:
    current_data.append(rfp_dict)

  # Save back
  with open(RFP_JSON_FILE, "w") as f:
    json.dump(current_data, f, indent=2)


async def process_rfp_pdf(file_path: str) -> dict:
  """
  Main pipeline: PDF -> Text -> Pydantic -> JSON and Neo4j
  """
  path_obj: Path = Path(file_path)
  if not path_obj.exists():
    raise FileNotFoundError(f"File not found: {file_path}")

  logger.info(f"Processing RFP: {path_obj.name}")

  text_content = extract_text_from_pdf(path_obj)
  if not text_content.strip():
    return {"status": "error", "message": "No text extracted from PDF"}

  rfp_structure: RFPStructure = await _extract_rfp_data(text_content)

  _save_to_json_file(rfp_structure)

  try:
    save_rfp_to_graph(rfp_structure)
  except Exception as e:
    logger.error(f"Neo4j ingestion failed: {e}")
    # We don't fail the whole request if DB sync fails, but we note it
    return {
      "status": "partial_success",
      "message": "Saved to JSON but failed to sync to Graph",
      "data": rfp_structure.model_dump(),
    }

  return {
    "status": "success",
    "message": f"RFP {rfp_structure.id} processed successfully",
    "data": rfp_structure.model_dump(),
  }
