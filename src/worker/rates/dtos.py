from pydantic import BaseModel


class Rates(BaseModel):
    source_iso_code: str
    timestamp: int
    data: dict[str, float]
