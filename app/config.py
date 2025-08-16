import os

from pydantic import BaseModel


class Settings(BaseModel):
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    tb_capacity: int = int(os.getenv("TB_CAPACITY", "20"))
    tb_rate: float = float(os.getenv("TB_RATE", "5"))  # tokens/sec
    bucket_prefix: str = os.getenv("BUCKET_PREFIX", "tb:user:")
    # NEW: how long (seconds) to retain in-memory metrics (must cover largest dashboard window)
    metrics_max_age_seconds: int = int(os.getenv("METRICS_MAX_AGE_SECONDS", "1800"))  # 30m

    def __init__(self, **data: object) -> None:
        super().__init__(**data)
        print("Config loaded:")
        print(f"  REDIS_URL={self.redis_url}")
        print(f"  TB_CAPACITY={self.tb_capacity}")
        print(f"  TB_RATE={self.tb_rate}")
        print(f"  BUCKET_PREFIX={self.bucket_prefix}")
        print(f"  METRICS_MAX_AGE_SECONDS={self.metrics_max_age_seconds}")


settings = Settings()
