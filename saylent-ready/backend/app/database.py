"""
Database configuration.

For the hackathon demo we use SQLite so the whole stack runs with zero
external services. In production (per the problem statement's
national-scale requirement) point DATABASE_URL at a managed Postgres
instance per BRICS member nation, with a central aggregation node that
only ever receives model weights (see app/ml/federated_learning.py),
never raw PHC records.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./project.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
