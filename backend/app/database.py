import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Only create engine on demand, not at import time
_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        # Skip connection if running tests (database will be created separately)
        if 'pytest' in sys.modules:
            return None
        _engine = create_engine(settings.DATABASE_URL)
    return _engine

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        if engine is None:
            return None  # In test mode
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal

Base = declarative_base()

def get_db():
    SessionLocal = get_session_local()
    if SessionLocal is None:
        return  # Skip in test mode
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
