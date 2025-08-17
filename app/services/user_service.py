import requests
import os
from dotenv import load_dotenv
import logging
from fastapi import HTTPException

load_dotenv()
logger = logging.getLogger("uvicorn")

# Server internal IPs: For server use only
USER_BE_ORIGIN = os.getenv("USER_BE_ORIGIN")
BASE_URL = f'{USER_BE_ORIGIN}/api/v1'

def user_login(username: str, password: str):
    logger.info("Making login request to User Service")
    url = f'{BASE_URL}/login/' 
    body = {
        "username": username,
        "password": password,
        "grant_type": "password",
        "scope": "",
        "client_id": "",
        "client_secret": ""
    }
    
    try:
        response = requests.post(url, data=body, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"User login failed with status {response.status_code}: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.json())

        logger.debug("User login successful")
        response_data = response.json()
        logger.debug(response_data)
        return response_data  # Return JSON data, not response object
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Failed to connect to User Service at {url}: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail="User authentication service is currently unavailable. Please try again later."
        )
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout connecting to User Service: {str(e)}")
        raise HTTPException(
            status_code=504, 
            detail="User authentication service timed out. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error during user login: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred during authentication."
        )