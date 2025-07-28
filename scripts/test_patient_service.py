# This script is used to test the patient service by fetching a patient by ID.
# "python -m scripts.test_patient_service"
# Note: Ensure to inclide BEARER_TOKEN in your own .env file!

import app.services.patient_service as patient_service
import os
from dotenv import load_dotenv
load_dotenv()

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
if __name__ == '__main__':

    get_patient_by_id_data = patient_service.get_patient_by_id(require_auth=True, bearer_token=BEARER_TOKEN, patient_id=1)

    print(f'GET PATIENT: {get_patient_by_id_data.json()}')

    get_patient_allocation_data = patient_service.get_patient_allocation_by_patient_id(require_auth=True, bearer_token=BEARER_TOKEN, patient_id=1)

    print(f'GET PATIENT ALLOCATION: {get_patient_allocation_data.json()}')