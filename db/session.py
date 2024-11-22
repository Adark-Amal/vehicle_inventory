from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.schema import Column
from typing import List
from contextlib import contextmanager
from .base import engine  # Import the engine created in base.py

# Create a session factory bound to the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def create_session():
    """
    Creates a new database session and ensures it is properly closed after use.
    Use this function in a `with` block to handle session cleanup automatically.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()  # Commit changes if no exceptions
    except Exception as e:
        session.rollback()  # Rollback changes if an exception occurs
        raise e
    finally:
        session.close()  # Close the session


def fetch_distinct_values(column: Column) -> List[str]:
    """
    Fetches distinct values from a specified column in the database.
    Args:
        column (Column): SQLAlchemy column from which to fetch distinct values.
    Returns:
        List[str]: A sorted list of unique values from the specified column.
    """
    with create_session() as session:
        return [
            row[0] for row in session.query(column).distinct().order_by(column).all()
        ]
