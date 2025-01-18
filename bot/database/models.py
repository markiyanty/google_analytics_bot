from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import BigInteger, String, Integer
from bot.config.settings import settings

# Database engine
engine = create_async_engine(
    url=settings.db_link,
    echo=True,
    future=True
)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class GoogleMeetGuest(Base):
    __tablename__ = 'google_meet_guests'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))

class JiraUser(Base):
    __tablename__ = 'jira_users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)  # User's name
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=True)  # Telegram ID
    email: Mapped[str] = mapped_column(String(100), nullable=True)  # User's email
    account_id: Mapped[str] = mapped_column(String(100), nullable=False)  # Jira account ID



async def async_main():
    """Create or update database schema."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)