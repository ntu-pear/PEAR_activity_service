import requests
import os
from dotenv import load_dotenv
import logging
from fastapi import HTTPException

load_dotenv()
logger = logging.getLogger("uvicorn")

# TO CLEAN UP AFTER TESTING
PATIENT_BE_ORIGIN = os.getenv("PATIENT_BE_ORIGIN")
PATIENT_BE_ORIGIN_NAT = os.getenv("PATIENT_BE_ORIGIN_NAT")
LOCAL_PATIENT_BE_ORIGIN = os.getenv("LOCAL_PATIENT_BE_ORIGIN")
BASE_URL = f'{PATIENT_BE_ORIGIN}/api/v1'
BASE_URL_NAT = f'{PATIENT_BE_ORIGIN_NAT}/api/v1'
BASE_URL_LOCAL = f'{LOCAL_PATIENT_BE_ORIGIN}/api/v1'

def get_patient_by_id(require_auth: bool, bearer_token: str, patient_id: int):
    url = f'{BASE_URL_NAT}/patients/{patient_id}'   # TO CLEAN UP AFTER TESTING
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
    url = f'{BASE_URL_LOCAL}/allocation/patient/{patient_id}?'      # TO CLEAN UP AFTER TESTING
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