from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///miaubox.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    requests = relationship("SavedRequest", back_populates="collection", cascade="all, delete-orphan")


class SavedRequest(Base):
    __tablename__ = "saved_requests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    method = Column(String, default="GET")
    url = Column(Text, default="")
    headers = Column(Text, default="{}")
    params = Column(Text, default="{}")
    body = Column(Text, default="")
    body_type = Column(String, default="json")
    auth_type = Column(String, default="none")
    auth_data = Column(Text, default="{}")
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=True)
    collection = relationship("Collection", back_populates="requests")
    created_at = Column(DateTime, default=datetime.utcnow)


class RequestHistory(Base):
    __tablename__ = "request_history"
    id = Column(Integer, primary_key=True, index=True)
    method = Column(String)
    url = Column(Text)
    status_code = Column(Integer)
    response_time = Column(Float)
    request_data = Column(Text)
    response_data = Column(Text)
    executed_at = Column(DateTime, default=datetime.utcnow)


class Environment(Base):
    __tablename__ = "environments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=False)
    variables = relationship("EnvVariable", back_populates="environment", cascade="all, delete-orphan")


class EnvVariable(Base):
    __tablename__ = "env_variables"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False)
    value = Column(Text, default="")
    is_secret = Column(Boolean, default=False)
    environment_id = Column(Integer, ForeignKey("environments.id"))
    environment = relationship("Environment", back_populates="variables")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
