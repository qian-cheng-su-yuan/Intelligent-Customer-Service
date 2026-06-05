from intelligent_customer_service.config import Settings
from intelligent_customer_service.database import initialize_database


if __name__ == "__main__":
    settings = Settings()
    initialize_database(settings.database_path, seed=True)
    print(f"Database initialized at {settings.database_path}")
