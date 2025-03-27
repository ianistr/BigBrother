from fastapi import FastAPI, Header, HTTPException,Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import uuid
from typing import Optional

API_KEY="ianisaremere"

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Use Railway's database connection string
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./local.db')

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Message Model
class MessageModel(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True)  # Use UUID as primary key
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Pydantic Model for Request Validation
class MessageCreate(BaseModel):
    content: str

# FastAPI App
app = FastAPI()

# Ensure tables are created
Base.metadata.create_all(bind=engine)

@app.post("/messages", dependencies=[Depends(verify_api_key)])
def create_message(message: MessageCreate):
    """
    Endpoint to post a new message
    Each message gets a unique ID and is stored in a separate row
    """
    db = SessionLocal()
    
    try:
        # Generate a unique ID for each message
        message_id = str(uuid.uuid4())
        
        # Create new message model instance
        db_message = MessageModel(
            id=message_id, 
            content=message.content
        )
        
        # Add to database and commit
        db.add(db_message)
        db.commit()
        
        return {
            "id": message_id, 
            "content": message.content, 
            "timestamp": db_message.timestamp
        }
   
    
    except Exception as e:
        # Rollback in case of error
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Close the session
        db.close()


@app.get("/messages", dependencies=[Depends(verify_api_key)])
def read_messages():
        db = SessionLocal()
        messages = db.query(MessageModel).all()
        db.close()
        return messages

@app.delete("/messages", dependencies=[Depends(verify_api_key)])
def delete_all_messages():
    """
    Endpoint to delete all messages from the database.
    This does not disable the database from receiving new messages.
    """
    db = SessionLocal()
    try:
        # Delete all messages
        deleted = db.query(MessageModel).delete()
        db.commit()
        return {"detail": f"All messages deleted successfully. Total deleted: {deleted}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()