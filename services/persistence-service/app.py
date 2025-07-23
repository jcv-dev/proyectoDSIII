import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Database Setup ---
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/db")
engine = sqlalchemy.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Model ---
class Link(Base):
    __tablename__ = "links"
    short_code = sqlalchemy.Column(sqlalchemy.String, primary_key=True, index=True)
    long_url = sqlalchemy.Column(sqlalchemy.String, index=True)

# Create table if it doesn't exist
Base.metadata.create_all(bind=engine)

# --- Pydantic Models ---
class LinkCreate(BaseModel):
    short_code: str
    long_url: HttpUrl

class LinkResponse(BaseModel):
    short_code: str
    long_url: HttpUrl

# --- FastAPI App ---
app = FastAPI()

@app.post("/links", response_model=LinkResponse, status_code=201)
def create_link(link: LinkCreate):
    db = SessionLocal()
    db_link = Link(short_code=link.short_code, long_url=str(link.long_url))
    db.add(db_link)
    try:
        db.commit()
        db.refresh(db_link)
    except sqlalchemy.exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Short code already exists.")
    finally:
        db.close()
    return db_link

@app.get("/links/{short_code}", response_model=LinkResponse)
def get_link(short_code: str):
    db = SessionLocal()
    db_link = db.query(Link).filter(Link.short_code == short_code).first()
    db.close()
    if db_link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    return db_link