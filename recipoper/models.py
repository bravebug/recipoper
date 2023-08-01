#!/usr/bin/env python
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.orm import mapped_column, relationship, sessionmaker
from sqlalchemy.types import String

class Base(DeclarativeBase):
    pass


class Recipe(Base):
    __tablename__ = "recipe_table"

    id:             Mapped[int]         = mapped_column(primary_key=True)
    name:           Mapped[str]         = mapped_column(index=True)
    ingredients:    Mapped[str]
    body:           Mapped[str]
    level_id:       Mapped[str]         = mapped_column(ForeignKey("level_table.id"))
    level:          Mapped["Level"]     = relationship()
    time:           Mapped[int]
    image:          Mapped[str]         = mapped_column(nullable=True)
    shown:          Mapped[int]         = mapped_column(default=0)
    votes:          Mapped[int]         = mapped_column(default=0)
    created:        Mapped[datetime]    = mapped_column(default=datetime.utcnow())

    @property
    def rating(self):
        return self.votes / self.shown

class Level(Base):
    __tablename__ = "level_table"

    id:     Mapped[int]         = mapped_column(primary_key=True)
    name:   Mapped[str]


def create_session(database_uri, echo=False):
    engine = create_engine(database_uri, echo=echo)
    Base.metadata.create_all(engine)
    return sessionmaker(engine)


if __name__ == "__main__":
    pass
    # Session = create_session(database_uri='sqlite:///:memory:', echo=True)
    # with Session.begin() as session:
    #     instance = Instance(name="test123")
    #     config = InstanceConfig(instance=instance, data=test_dict)
    #     session.add(config)
