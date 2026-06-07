import requests
import os
from dotenv import load_dotenv
import logging
from fastapi import HTTPException

load_dotenv()
logger = logging.getLogger("uvicorn")

# Server internal IPs: For server use only
PATIENT_BE_ORIGIN = os.getenv("PATIENT_BE_ORIGIN")
BASE_URL = f'{PATIENT_BE_ORIGIN}/api/v1'

def get_patient_by_id(require_auth: bool, bearer_token: str, patient_id: int):
    url = f'{BASE_URL}/patients/{patient_id}'
    params = {"require_auth": f"{require_auth}", "mask": "true"}
    headers = None
    if require_auth:
        headers = {"Authorization": f"Bearer {bearer_token}"}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    logger.debug("\nGet Patient by ID response body:")
    logger.debug(response.json())  # Try to parse as JSON
    return response

def get_patient_allocation_by_patient_id(require_auth: bool, bearer_token: str, patient_id: int):
    url = f'{BASE_URL}/allocation/patient/{patient_id}?' 
    params = {"require_auth": f"{require_auth}"}
    headers = None
    if require_auth:
        headers = {"Authorization": f"Bearer {bearer_token}"}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    logger.debug("\nGet Patient Allocation by Patient ID response body:")
    logger.debug(response.json())  # Try to parse as JSON
    return response

def get_patient_name(patient_id: int, bearer_token: str = "") -> str:
    """
    Get patient full name by ID
    """
    try:
        patient_data = get_patient_by_id(
            require_auth=True,
            bearer_token=bearer_token,
            patient_id=patient_id,
        )

        if patient_data.status_code == 200:
            patient_json = patient_data.json()
            return patient_json.get("data", {}).get("name", "Unknown")

    except Exception:
        pass
    return 'Unknown'