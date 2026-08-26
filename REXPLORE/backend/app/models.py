"""
ORM models: Papers, PaperSections, PaperFeatures, Datasets, QueryHistory,
QuerySources, SyntheticDatasets.
"""
import datetime as dt

from sqlalchemy import (
    Column, Integer, String, Text, Float, ForeignKey, DateTime, JSON, Boolean
)
from sqlalchemy.orm import relationship

from app.database import Base


def now():
    return dt.datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    affiliation = Column(String, nullable=True)
    avatar_data = Column(Text, nullable=True)  # data URI (small, resized client-side)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    papers = relationship("Paper", back_populates="owner", cascade="all, delete-orphan")

    @property
    def avatar_url(self):
        return self.avatar_data


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False, unique=True)
    file_path = Column(String, nullable=False)
    title = Column(String, nullable=True)
    page_count = Column(Integer, default=0)
    status = Column(String, default="uploading")  # uploading, reading, extracting, ready, error
    status_detail = Column(String, default="")
    error_message = Column(Text, nullable=True)
    used_ocr = Column(Boolean, default=False)
    research_domain = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=now)
    processed_at = Column(DateTime, nullable=True)

    sections = relationship("PaperSection", back_populates="paper", cascade="all, delete-orphan")
    features = relationship("PaperFeature", back_populates="paper", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="paper", cascade="all, delete-orphan")
    queries = relationship("QueryHistory", back_populates="paper", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="papers")


class PaperSection(Base):
    __tablename__ = "paper_sections"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    page_number = Column(Integer, nullable=True)
    order_index = Column(Integer, default=0)
    raw_text = Column(Text, default="")
    key_points = Column(JSON, default=list)          # list[str]
    simple_explanation = Column(Text, default="")
    concepts = Column(JSON, default=list)             # list[str]
    findings = Column(JSON, default=list)              # list[str]

    paper = relationship("Paper", back_populates="sections")


class PaperFeature(Base):
    __tablename__ = "paper_features"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    feature_type = Column(String, nullable=False)  # algorithm, dataset, metric, concept, keyword, technique, technology
    value = Column(String, nullable=False)
    context = Column(Text, default="")
    page_number = Column(Integer, nullable=True)
    confidence = Column(Float, default=0.5)

    paper = relationship("Paper", back_populates="features")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    mentioned_name = Column(String, nullable=False)     # name as found in the paper
    kind = Column(String, default="not_found")           # original, alternative, synthetic, not_found
    status = Column(String, default="unresolved")         # available, unavailable, unresolved
    name = Column(String, nullable=True)
    repository = Column(String, nullable=True)
    doi = Column(String, nullable=True)
    url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    relevance_reason = Column(Text, nullable=True)       # populated for alternatives
    searched_at = Column(DateTime, nullable=True)

    paper = relationship("Paper", back_populates="datasets")
    synthetic_versions = relationship("SyntheticDataset", back_populates="dataset", cascade="all, delete-orphan")


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    retrieval_method = Column(String, default="semantic")  # semantic, keyword_fallback
    created_at = Column(DateTime, default=now)

    paper = relationship("Paper", back_populates="queries")
    sources = relationship("QuerySource", back_populates="query", cascade="all, delete-orphan")


class QuerySource(Base):
    __tablename__ = "query_sources"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("query_history.id"), nullable=False, index=True)
    section_name = Column(String, nullable=False)
    page_number = Column(Integer, nullable=True)
    snippet = Column(Text, default="")
    score = Column(Float, default=0.0)

    query = relationship("QueryHistory", back_populates="sources")


class SyntheticDataset(Base):
    __tablename__ = "synthetic_datasets"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    row_count = Column(Integer, nullable=False)
    columns = Column(JSON, default=list)   # list[{"name": str, "type": str}]
    seed = Column(Integer, default=42)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=now)

    dataset = relationship("Dataset", back_populates="synthetic_versions")
