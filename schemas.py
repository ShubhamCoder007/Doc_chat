from pydantic import BaseModel, Field

class BoolResult(BaseModel):
    bool_result: bool = Field(description="the boolean result")

class QueryRefined(BaseModel):
    query: str = Field(description="the refined query")