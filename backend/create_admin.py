
from getpass import getpass

from database import SessionLocal
from models import User
from auth import hash_password


def create_first_admin():
    db = SessionLocal()

    try:
        existing_admin = db.query(User).filter(
            User.role == "admin"
        ).first()

        if existing_admin:
            print("An administrator account already exists.")
            return

        print("\n=== SmartTriage First Administrator Setup ===")

        full_name = input("Administrator name: ").strip()
        email = input("Administrator email: ").strip().lower()

        if not full_name or not email:
            print("Name and email are required.")
            return

        password = getpass("Create password (minimum 12 characters): ")
        confirm_password = getpass("Confirm password: ")

        if len(password) < 12:
            print("Password must contain at least 12 characters.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        existing_user = db.query(User).filter(
            User.email == email
        ).first()

        if existing_user:
            print("This email is already registered.")
            return

        admin = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            role="admin",
            is_active=True
        )

        db.add(admin)
        db.commit()

        print("\nAdministrator account created successfully.")
        print(f"Name: {full_name}")
        print(f"Email: {email}")
        print("Role: admin")

    except Exception as error:
        db.rollback()
        print("Administrator creation failed.")
        print(error)

    finally:
        db.close()


if __name__ == "__main__":
    create_first_admin()
