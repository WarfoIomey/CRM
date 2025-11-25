import os
from dotenv import load_dotenv


load_dotenv()


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    )
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '5432')
    DB_USER: str = os.getenv('POSTGRES_USER', 'postgres')
    DB_PASS: str = os.getenv('POSTGRES_PASSWORD', 'password')
    DB_NAME: str = os.getenv('POSTGRES_DB', 'crm_db')

    @property
    def database_url(self) -> str:
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


settings = Settings()
