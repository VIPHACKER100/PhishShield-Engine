from typing import Optional
from pydantic import BaseModel, Field, field_validator

MAX_TEXT_LENGTH = 50_000

class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    model: Optional[str] = None
    headers: Optional[str] = ""

    @field_validator("text")
    @classmethod
    def sanitise(cls, v: str) -> str:
        return v.strip()

class BatchPredictRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    emails: list[str] = Field(..., min_length=1, max_length=100)
    model_name: Optional[str] = None

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)

class LoginRequest(BaseModel):
    username: str
    password: str

class FeedbackRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    email_text: str = Field(..., min_length=1)
    predicted_label: str
    correct_label: str
    model_used: str = "unknown"
