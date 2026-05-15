import secrets
import os
from typing import Optional
from Brain import Brain

from fastapi import FastAPI, Header, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import platform
import multiprocessing
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(">")
from config_driver import Check_Keys

# -------------------------------
# Load Configs
# -------------------------------
MONGODB_URL = Check_Keys("KEYS", "MONGODB_URL")

# -------------------------------
# MongoDB Setup
# -------------------------------
client = MongoClient(MONGODB_URL)
db = client["FridayDB"]
api_keys_collection = db["api_keys"]

# -------------------------------
# FastAPI Setup
# -------------------------------
app = FastAPI(title="Friday 2.0 Secure Protocol -> SERVER RUNNING...")

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

# -------------------------------
# Models
# -------------------------------
class ChatRequest(BaseModel):
    query: str
    source: str

class KeyCreate(BaseModel):
    owner: str
    client_type: str  # mobile / web / server


# def Brain(text: str, source='server'):
#     return f"Friday processed: {text}"

# -------------------------------
# API Key Verification
# -------------------------------
async def verify_api_key(
    authorization: Optional[str] = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = authorization.split(" ")[1]

    db_key = api_keys_collection.find_one({
        "key": token,
        "is_active": True
    })

    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or inactive API Key"
        )

    return db_key

# -------------------------------
# Admin: Generate API Key
# -------------------------------
@app.post("/admin/generate-key")
def create_key(data: KeyCreate):

    if data.client_type not in ["mobile", "web", "server"]:
        raise HTTPException(status_code=400, detail="Invalid client type")

    new_key = f"FR_{secrets.token_urlsafe(32)}"

    api_keys_collection.insert_one({
        "key": new_key,
        "owner": data.owner,
        "client_type": data.client_type,
        "is_active": True,
    })

    return {
        "api_key": new_key,
        "client_type": data.client_type,
        "info": "Save this key securely!"
    }

# -------------------------------
# Chat Endpoint
# -------------------------------
@app.post("/chat")
@limiter.limit("100/day")
async def chat_endpoint(
    request: Request,
    data: ChatRequest,
    current_key: dict = Depends(verify_api_key)
):
    response_text = Brain(data.query, source=current_key["client_type"])

    return {
        "reply": response_text,
        "user": current_key["owner"],
        "source": current_key['client_type']
    }

# -------------------------------
# Health Check
# -------------------------------
@app.get("/")
def health_check():
    return {
        "status": "Friday 2.0 Protocol Server Online.",
    }


@app.on_event("startup")
async def startup_event():
    # ANSI Escape Codes for Terminal Colors
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    print("\n")
    print(f"{CYAN}{BOLD}Initializing Core Systems...{RESET}")
    print(f"{MAGENTA}F.R.I.D.A.Y. - Friendly Reliable Intelligent Digital Assistant for Youth{RESET}")
    
    # ASCII Art in Cyan
    print(f"{CYAN}{BOLD}")
    print("╔══════════════════════════════════════════════════════╗")
    print("║                                                      ║")
    print("║   ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗       ║")
    print("║   ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝       ║")
    print("║   █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝        ║")
    print("║   ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝         ║")
    print("║   ██║     ██║  ██║██║██████╔╝██║  ██║   ██║          ║")
    print("║   ╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝          ║")
    print("║                                                      ║")
    print("║   ⚡ Friendly Reliable Intelligent Agent ⚡          ║")
    print("║                                                      ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(RESET)
    
    # Creator and Status Banner
    print(f"| {BOLD}Creator:{RESET} {YELLOW}Shubham{RESET} | {BOLD}System Status:{RESET} {GREEN}ONLINE{RESET} | {BOLD}Version:{RESET} {GREEN}2.0{RESET} |")
    print("=" * 60)
    
    # System Specs (Left Aligned for clean HUD look)
    print(f" 💻 {BOLD}Host OS:{RESET}             {platform.system()} {platform.release()}")
    print(f" 🧮 {BOLD}Processing Threads:{RESET}  {multiprocessing.cpu_count()} Cores Available")
    print(f" 📂 {BOLD}Neural Pathways:{RESET}     {os.getcwd()}")
    print("-" * 60)
    
    # Subsystem Status Array
    print(f" 🌐 {CYAN}Multi-Frontend:{RESET}      [{GREEN}ENABLED{RESET}]")
    print(f" ⚡ {CYAN}Async Event Loop:{RESET}    [{GREEN}RUNNING{RESET}]")
    print(f" 🔄 {CYAN}Concurrency:{RESET}         [{GREEN}READY{RESET}]")
    print(f" 🧠 {CYAN}AI Brain Status:{RESET}     [{GREEN}STABLE{RESET}]")
    print(f" 📦 {CYAN}Tools & Modules:{RESET}     [{GREEN}100% LOADED{RESET}]")
    print(f" 🔐 {CYAN}Permission Layer:{RESET}    [{GREEN}ACTIVE{RESET}]")
    print("=" * 60)
    
    # Final Ready Prompt
    print(f"\n 🤖 {BOLD}{MAGENTA}Friday is LIVE and ready to assist you, Shubham!{RESET}\n")

# -------------------------------
# Run Server
# -------------------------------
if __name__ == "__main__":
    # 157.33.56.181
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)