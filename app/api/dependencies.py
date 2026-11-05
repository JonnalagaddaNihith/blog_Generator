from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db


def get_current_db(session: AsyncSession = Depends(get_db)):
    """Dependency to get database session."""
    return session
