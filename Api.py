import secrets
from datetime import datetime
from typing import Optional
from Brain import Brain

from fastapi import FastAPI, Header, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# --- 1. Database Setup (SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///Database\\Tokens\\Friday_Key.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class APIKeyDB(Base):
    __tablename__ = "api_keys"
    key = Column(String, primary_key=True, index=True)
    owner = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- 2. FastAPI & Rate Limiter Setup ---
app = FastAPI(title="Friday 2.0 Secure Protocol")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Dependency & Models ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    site_id: str
    message: str
    knowledge_base_id: Optional[str] = "default"

class KeyCreate(BaseModel):
    owner: str

# --- 4. Security Logic ---
async def verify_api_key(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing or invalid Authorization header"
        )
    
    token = authorization.split(" ")[1]
    db_key = db.query(APIKeyDB).filter(APIKeyDB.key == token, APIKeyDB.is_active == True).first()
    
    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid or inactive API Key"
        )
    return db_key

# --- 5. Friday Brain (Placeholder) ---
def process_with_brain(text: str):
    response = Brain(text)
    return f"Friday: {response}"



@app.post("/admin/generate-key")
def create_key(data: KeyCreate, db: Session = Depends(get_db)):
    """Admin endpoint to generate a new secure API Key"""
    new_key = f"sk_fri_{secrets.token_urlsafe(32)}"
    db_item = APIKeyDB(key=new_key, owner=data.owner)
    db.add(db_item)
    db.commit()
    return {"api_key": new_key, "owner": data.owner, "info": "Save this key, it won't be shown again!"}

@app.post("/chat")
@limiter.limit("10/minute")
async def chat_endpoint(
    request: Request, 
    data: ChatRequest, 
    current_key: APIKeyDB = Depends(verify_api_key)
):
    try:
        response_text = process_with_brain(data.message)
        return {
            "reply": response_text,
            "site_id": data.site_id,
            "kb_id": data.knowledge_base_id,
            "user": current_key.owner
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Brain Error")

@app.get("/")
def health_check():
    return {"status": "Friday 2.0 Protocol Online", "timestamp": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)