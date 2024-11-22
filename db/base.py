from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from config import current_config

# Initialize the SQLAlchemy Base class
Base = declarative_base()

# Create the database engine using the configured database URI
engine = create_engine(current_config.SQLALCHEMY_DATABASE_URI, echo=True)
