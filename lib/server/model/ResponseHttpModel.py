# Define the data models
from pydantic import BaseModel, Field
from typing import Optional, List

class ResponseHttp(BaseModel):
    status_code: int
    content: dict