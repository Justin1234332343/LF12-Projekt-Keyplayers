from pydantic import BaseModel
import os

class Settings(BaseModel):
    ORDS_BASE_URL: str = os.getenv("ORDS_BASE_URL", "http://ords:8080/ords/lf12")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")  # nicht 8181 ;)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

settings = Settings()
