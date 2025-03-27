from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Use Railway's database connection string
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./local.db')

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Data Model
class DataEntry(Base):
    __tablename__ = "entries"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Model for Validation
class EntryModel(BaseModel):
    key: str
    value: str

# Create FastAPI App
app = FastAPI()

# Ensure tables are created
Base.metadata.create_all(bind=engine)

@app.put("/entries/{key}")
def create_or_update_entry(key: str, entry: EntryModel):
    """
    Create or update an entry with a specific key
    """
    db = SessionLocal()
    
    try:
        # Check if entry exists
        existing_entry = db.query(DataEntry).filter(DataEntry.key == key).first()
        
        if existing_entry:
            # Update existing entry
            existing_entry.value = entry.value
        else:
            # Create new entry
            new_entry = DataEntry(key=key, value=entry.value)
            db.add(new_entry)
        
        db.commit()
        return {"key": key, "value": entry.value, "status": "success"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/entries/{key}")
def get_entry(key: str):
    """
    Retrieve an entry by key
    """
    db = SessionLocal()
    
    try:
        entry = db.query(DataEntry).filter(DataEntry.key == key).first()
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        return {"key": entry.key, "value": entry.value}
    
    finally:
        db.close()