from sqlalchemy import create_engine, Column, String, Date, UniqueConstraint, Integer
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Change(Base):
    __tablename__ = "changes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    krs = Column(String, nullable=False)
    change_date = Column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint("krs", "change_date"),
    )
def init_db(db_path = "Azkaban.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

Session = init_db()