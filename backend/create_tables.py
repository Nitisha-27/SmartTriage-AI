
from database import engine, Base
import models  # Registers Case and AuditLog models


def create_tables():
    try:
        Base.metadata.create_all(bind=engine)

        print("DATABASE TABLES CREATED SUCCESSFULLY")

        for table in Base.metadata.sorted_tables:
            print(f"Table created: {table.name}")

    except Exception as error:
        print("TABLE CREATION FAILED")
        print(error)


if __name__ == "__main__":
    create_tables()
