import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

Base = declarative_base()
engine = sa.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    discord_id = sa.Column(sa.BigInteger, unique=True, nullable=False)
    username = sa.Column(sa.String(100), nullable=False)
    xp = sa.Column(sa.Integer, default=0)
    level = sa.Column(sa.Integer, default=1)
    message_count = sa.Column(sa.Integer, default=0)
    created_at = sa.Column(sa.DateTime, default=sa.func.now())


class UserStats(Base):
    __tablename__ = 'user_stats'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    command_count = sa.Column(sa.Integer, default=0)
    last_active = sa.Column(sa.DateTime, default=sa.func.now())


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()