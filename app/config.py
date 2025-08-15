from pydantic import BaseModel
import os

class Settings(BaseModel):
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    tb_capacity: int = int(os.getenv("TB_CAPACITY", "20"))
    tb_rate: float = float(os.getenv("TB_RATE", "20"))  # tokens/sec
    bucket_prefix: str = os.getenv("BUCKET_PREFIX", "tb:user:")

    def __init__(self, **data):
        super().__init__(**data)
        print("Config loaded:")
        print(f"  REDIS_URL={self.redis_url}")
        print(f"  TB_CAPACITY={self.tb_capacity}")
        print(f"  TB_RATE={self.tb_rate}")
        print(f"  BUCKET_PREFIX={self.bucket_prefix}")

settings = Settings()
