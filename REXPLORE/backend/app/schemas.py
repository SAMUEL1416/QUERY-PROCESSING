"""
Pydantic schemas used for request validation and response serialization.
"""
import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


# ---------- Auth ----------

class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name is required.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    affiliation: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: dt.datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    affiliation: Optional[str] = Field(default=None, max_length=200)

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name is required.")
        return v

    @field_validator("affiliation")
    @classmethod
    def strip_affiliation(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None


class EmailUpdateRequest(BaseModel):
    new_email: EmailStr
    current_password: str = Field(min_length=1, max_length=128)


class PasswordUpdateRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_new_password: str = Field(min_length=8, max_length=128)


class DeleteAccountRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)


# ---------- Papers ----------

class PaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    title: Optional[str]
    page_count: int
    status: str
    status_detail: str
    error_message: Optional[str] = None
    used_ocr: bool
    research_domain: Optional[str]
    uploaded_at: dt.datetime
    processed_at: Optional[dt.datetime]


class PaperDetailOut(PaperOut):
    sections: List["PaperSectionOut"] = []
    features: List["PaperFeatureOut"] = []


# ---------- Sections / Features ----------

class PaperSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    page_number: Optional[int]
    order_index: int
    key_points: List[str] = []
    simple_explanation: str = ""
    concepts: List[str] = []
    findings: List[str] = []


class PaperFeatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    feature_type: str
    value: str
    context: str = ""
    page_number: Optional[int]
    confidence: float


# ---------- Queries ----------

class QueryCreate(BaseModel):
    paper_id: int
    question: str = Field(min_length=3, max_length=1000)


class QuerySourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_name: str
    page_number: Optional[int]
    snippet: str
    score: float


class QueryAnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query_text: str
    answer_text: str
    retrieval_method: str
    created_at: dt.datetime
    sources: List[QuerySourceOut] = []


# ---------- Datasets ----------

class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mentioned_name: str
    kind: str
    status: str
    name: Optional[str]
    repository: Optional[str]
    doi: Optional[str]
    url: Optional[str]
    description: Optional[str]
    relevance_reason: Optional[str]
    searched_at: Optional[dt.datetime]


class SyntheticColumnSpec(BaseModel):
    name: str
    type: str = Field(pattern="^(integer|float|category|boolean|date|text)$")
    categories: Optional[List[str]] = None  # required if type == category


class SyntheticDatasetCreate(BaseModel):
    row_count: int = Field(gt=0, le=100000)
    columns: List[SyntheticColumnSpec]
    seed: int = 42


class SyntheticDatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    row_count: int
    columns: list
    seed: int
    created_at: dt.datetime
    preview: List[dict] = []


# ---------- Analytics ----------

class AnalyticsOverviewOut(BaseModel):
    papers_analyzed: int
    datasets_discovered: int
    features_extracted: int
    queries_processed: int
    sections_extracted: int
    algorithms_count: int
    metrics_count: int
    concepts_count: int


class DistributionItem(BaseModel):
    label: str
    count: int


class AnalyticsFeaturesOut(BaseModel):
    algorithm_distribution: List[DistributionItem]
    metric_distribution: List[DistributionItem]
    dataset_availability: List[DistributionItem]
    concept_distribution: List[DistributionItem]


# ---------- Comparison ----------

class ComparisonRequest(BaseModel):
    paper_ids: List[int] = Field(min_length=2, max_length=6)


PaperDetailOut.model_rebuild()
