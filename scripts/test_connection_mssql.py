# This script tests the database connection using the env vars and configs defined in app/database.py.
# Run this script to test connection using:
# "python -m scripts.test_connection_mssql"
from app.database import engine
import sqlalchemy as sa

def test_db_connection():
    """Test the database connection using the current SQLAlchemy engine from app.database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(sa.text("SELECT @@version;"))
            for row in result:
                print(row[0])
        print("Connection successful.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_db_connection()
