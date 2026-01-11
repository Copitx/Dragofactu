from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

def get_database_url():
    return os.getenv('DATABASE_URL', 'postgresql://localhost:5432/dragofactu')

def create_engine_instance():
    database_url = get_database_url()
    
    if database_url.startswith('sqlite'):
        engine = create_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=os.getenv('DEBUG', 'false').lower() == 'true'
        )
    else:
        engine = create_engine(
            database_url,
            echo=os.getenv('DEBUG', 'false').lower() == 'true'
        )
    
    return engine

engine = create_engine_instance()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()