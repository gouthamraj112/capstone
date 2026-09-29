from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class QueryRequest(BaseModel):
    question: Optional[str] = Field(default=None, max_length=1000)
    query: Optional[str] = Field(default=None, max_length=1000)
    language: str = Field(default="en")
    start_date: Optional[str] = Field(default=None)
    end_date: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def check_question(self):
        if not self.question and self.query:
            self.question = self.query
        if not self.question or len(self.question.strip()) < 3:
            raise ValueError("question or query must be provided with at least 3 characters")
        return self


class AgentRunRequest(BaseModel):
    task: Optional[str] = Field(default="insights")
    query: Optional[str] = Field(default=None)
    question: Optional[str] = Field(default=None)
    hours: int = Field(default=6, ge=1, le=168)
    language: str = Field(default="en")
    start_date: Optional[str] = Field(default=None)
    end_date: Optional[str] = Field(default=None)


class QueryResponse(BaseModel):
    success: bool
    question: str
    intent: str
    answer: str
    agents_used: list[str]
    evidence: list[dict]
    chart_data: list[dict]
    confidence: float = Field(ge=0, le=1)
    trace_id: str
    llm_provider: str
    language: str = "en"
    is_relevant: bool = True
    warning: Optional[str] = None
    suggested_queries: list[str] = Field(default_factory=list)
    chart_type: Optional[str] = None
    chart_title: Optional[str] = None
    citations: list[dict] = Field(default_factory=list)
    evaluation: Optional[dict] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
