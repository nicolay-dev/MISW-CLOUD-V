"""Database engine & session creation."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from os import getenv

load_dotenv()

engine = create_engine(getenv("DATABASE_URL"), echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()