# PEAR Activity Service

## Overview

PEAR Activity Service is a microservice for managing activity-related data. This repository provides the setup and development instructions to get the service running locally.

## Getting Started

### Prerequisites
1. **Git**: Ensure Git is installed on your system.
2. **Conda**: Install Conda for managing virtual environments.
3. **NTU VPN**: Install the NTU VPN to access internal resources.


### Connect to NTU VPN
To connect to the NTU VPN, follow these steps:

Network Connection: Ensure you are connected to the NTUSECURE Wi-Fi network or connect through the NTU VPN.

VPN Setup: Follow the [installation guide](https://fyppear.atlassian.net/wiki/spaces/FP/pages/129794049/Setup+Instructions+Developers) for detailed instructions on setting up and connecting to the VPN.

### Cloning the Repository
Clone the repository using the following command:

```bash
git clone https://github.com/ntu-pear/PEAR_activity_service.git
cd PEAR_activity_service
```

### Setting Up Your Environment
1. Create a Conda Virtual Environment:
```bash
# This is to set the python version in your conda environment to 3.9.19
conda create -n pear_activity_service python=3.9.19
conda activate pear_activity_service
```
### Install the required dependencies
```bash
#install the necessary requirements in the conda environment
pip install -r requirements.txt
```

### Environment Configuration
Make sure to create a .env file in the PEAR_activity_service folder. For instructions on how to configure this file, refer to the Confluence page:

Click on the link to be redirect to the confluence page -->[Confluence page](https://fyppear.atlassian.net/wiki/spaces/FP/pages/132939777/Environment+Configuration+-+.env+File)

### Running the Application 
After the installation is completed, run the application on your machine
```bash
uvicorn app.main:app --reload
```

This will start the microservice, which should be accessible at `http://localhost:8000`.

### Notes for Windows Users
Ensure that Visual Studio Code uses LF (Line Feed) instead of CRLF (Carriage Return Line Feed) for line endings.

### Notes for Mac Users
There will be a lot of unresolved troubleshooting. If the application does not work, run this command in the current directory
```bash
#install the necessary requirements in the conda environment
pip install -r requirements.txt

#After the installation is completed, run the application on your machine
uvicorn app.main:app --reload
```


### Troubleshooting
If you encounter issues with Docker Compose, such as missing `.sh` files, you may need to adjust Git's line ending settings:
```bash
git config core.autocrlf false
git rm --cached -r .
git reset --hard
```

After running these commands, you should see:
```bash
Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

This indicates that the service is running successfully.

### Versions Used
For consistency and reproducibility, the following versions of packages are used in this project:

- Python: 3.9.19
- FastAPI: 0.111.1
- Pydantic: 2.8.2
- Psycopg2-binary: 2.9.9
- Databases: 0.9.0
- SQLAlchemy: 2.0.31
- PyODBC: 5.1.0
- Uvicorn: 0.30.3
- Python-dotenv: 1.0.1

### Additional Information

- MSSQL Database Name: `fyp_activity_service_dev`
- Microservice Name: `activity_service`