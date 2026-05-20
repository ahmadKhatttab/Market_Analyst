from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "sqlite:///opensooq_data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    import models 
    Base.metadata.create_all(bind=engine)