#!/usr/bin/env python

from models import Recipe, Level
from models import create_session
from sqlalchemy import select, update
from sqlalchemy.sql import func


class DataBase:
    def __init__(self, database_uri, echo):
        self.Session = create_session(database_uri=database_uri, echo=echo)
        with self.Session.begin() as session:
            if not session.query(Level).first():
                for name in ("Лёгкий", "Средний", "Сложный"):
                    level = Level(name=name)
                    session.add(level)

    def add_recipe(self, name: str, ingredients: str, body: str, level_id: int, time: int, image: str = None):
        with self.Session.begin() as session:
            recipe = Recipe(name=name, ingredients=ingredients, body=body, level_id=level_id, time=time, image=image)
            session.add(recipe)

    def list_levels(self):
        with self.Session.begin() as session:
            query = select(Level.id, Level.name)
            return session.execute(query).all()

    def list_recipe_ids(self, level_ids: list = None):
        with self.Session.begin() as session:
            if level_ids:
                query = session.query(Recipe).filter(Recipe.level_id.in_(level_ids))
            else:
                query = session.query(Recipe)
            return [recipe.id for recipe in query.all()]

    def get_recipe_by_id(self, id_):
        with self.Session.begin() as session:
            recipe = session.query(Recipe).filter(Recipe.id == id_).one()
            recipe.shown += 1
            max_rating = float(session.query(func.max(Recipe.votes / Recipe.shown + 1)).scalar())
            rating = int(100 / max_rating * recipe.rating + 0.5)
            return (
                recipe.id,
                recipe.name,
                recipe.ingredients,
                recipe.body,
                recipe.level.name,
                recipe.time,
                recipe.image,
                recipe.shown,
                recipe.votes,
                rating,
            )

    def vote_recipe_by_id(self, id_):
        with self.Session.begin() as session:
            recipe = session.query(Recipe).filter(Recipe.id == id_).one()
            recipe.votes += 1
            return recipe.votes


if __name__ == "__main__":
    db = DataBase(database_uri='sqlite:///:memory:', echo=True)
    # print(db.list_levels())
    db.add_recipe("Яйцо всухомятку", "1. Взять яйцо\n2. Грызть", 1)
    db.add_recipe("Яйцо Пашот", "Разбить яйцо в кипяток с уксусом", 1)
    print(db.list_recipe_ids())
    breakpoint()
    # print(db.list_recipe_ids([1]))
    # print(db.list_recipe_ids([2]))
    # print(db.get_recipe_by_id(1))
