
from sqlalchemy import text
from database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user, version()")
        )

        database, user, version = result.fetchone()

        print("POSTGRESQL CONNECTION SUCCESSFUL")
        print("Database:", database)
        print("User:", user)
        print("Version:", version.split(",")[0])

except Exception as error:
    print("DATABASE CONNECTION FAILED")
    print(error)
