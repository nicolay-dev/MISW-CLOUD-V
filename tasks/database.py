"""Database engine & session creation."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine('postgresql://misoadmin:miso1234@localhost:5432/cloudtask')
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()