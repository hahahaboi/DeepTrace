import os

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgrespassword@db:5432/deeptrace")
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "deeptrace_secret_123")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
