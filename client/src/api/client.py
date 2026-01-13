import httpx

from config import API_BASE_URL

TIMEOUT = 60.0  # PDF processing can take time


def get_programmers(status: str | None = None) -> list[dict]:
  params = {"status": status} if status else {}
  with httpx.Client(timeout=TIMEOUT) as client:
    response = client.get(f"{API_BASE_URL}/entities/programmers", params=params)
    response.raise_for_status()
    return response.json()


def get_projects() -> list[dict]:
  with httpx.Client(timeout=TIMEOUT) as client:
    response = client.get(f"{API_BASE_URL}/entities/projects")
    response.raise_for_status()
    return response.json()


def get_rfps() -> list[dict]:
  with httpx.Client(timeout=TIMEOUT) as client:
    response = client.get(f"{API_BASE_URL}/entities/rfps")
    response.raise_for_status()
    return response.json()


def upload_cv(filename: str, content: bytes) -> dict:
  with httpx.Client(timeout=TIMEOUT) as client:
    files = {"file": (filename, content, "application/pdf")}
    response = client.post(f"{API_BASE_URL}/ingest/cv/upload", files=files)
    response.raise_for_status()
    return response.json()


def upload_rfp(filename: str, content: bytes) -> dict:
  with httpx.Client(timeout=TIMEOUT) as client:
    files = {"file": (filename, content, "application/pdf")}
    response = client.post(f"{API_BASE_URL}/ingest/rfp/upload", files=files)
    response.raise_for_status()
    return response.json()


def upload_projects(filename: str, content: bytes) -> dict:
  with httpx.Client(timeout=TIMEOUT) as client:
    files = {"file": (filename, content, "application/json")}
    response = client.post(f"{API_BASE_URL}/ingest/projects/upload", files=files)
    response.raise_for_status()
    return response.json()


def get_graph_stats() -> dict:
  with httpx.Client(timeout=TIMEOUT) as client:
    response = client.get(f"{API_BASE_URL}/info/stats")
    response.raise_for_status()
    return response.json()


def get_node_sample(label: str) -> list[dict]:
  with httpx.Client(timeout=TIMEOUT) as client:
    response = client.get(f"{API_BASE_URL}/info/sample", params={"label": label})
    response.raise_for_status()
    return response.json()


def query_knowledge_graph(question: str) -> dict:
  with httpx.Client(timeout=TIMEOUT) as client:
    response = client.post(f"{API_BASE_URL}/query/", json={"question": question})
    response.raise_for_status()
    return response.json()


def get_example_queries() -> dict[str, list[str]]:
  with httpx.Client(timeout=TIMEOUT) as client:
    response = client.get(f"{API_BASE_URL}/query/examples")
    response.raise_for_status()
    return response.json()


def find_matches(rfp_id: str, threshold_months: int = 1) -> dict:
  with httpx.Client(timeout=TIMEOUT) as client:
    response = client.get(
      f"{API_BASE_URL}/match/{rfp_id}",
      params={"threshold_months": threshold_months},
    )
    response.raise_for_status()
    return response.json()


def confirm_assignment(rfp_id: str, programmer_ids: list[str]) -> dict:
  with httpx.Client(timeout=TIMEOUT) as client:
    response = client.post(
      f"{API_BASE_URL}/match/{rfp_id}/confirm",
      json={"programmer_ids": programmer_ids},
    )
    response.raise_for_status()
    return response.json()
