import os

from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = f"http://localhost:{os.getenv('SERVER_PORT', '8032')}/api/v1"
