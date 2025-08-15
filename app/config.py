
from pydantic import BaseModel
import os

class Settings(BaseModel):
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    tb_capacity: int = int(os.getenv("TB_CAPACITY", "20"))
    tb_rate: float = float(os.getenv("TB_RATE", "20"))  # tokens/sec
    bucket_prefix: str = os.getenv("BUCKET_PREFIX", "tb:user:")

settings = Settings()
