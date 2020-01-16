from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Events import Base, Category, Event, Tag, EventTag

_DEFAULT_DBNAME = 'lifemanager'


def create_database(db_name):

    engine = create_engine('sqlite:///{}.sqlite'.format(db_name))
    sessionm = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    return sessionm


def initialize_database(db_name=_DEFAULT_DBNAME):

    sess = get_session(db_name)

    # Populate existing event categories
    known_categories = ['task', 'action', 'event']

    db_categories = Category.select_all(sess)
    existing_categories = [cat.name for cat in db_categories]
    for kc in known_categories:

        if kc not in existing_categories:
            cat = Category(name=kc)
            cat.add_to_db(sess)

    return sess


def drop_database(db_name=_DEFAULT_DBNAME):

    engine = create_engine('sqlite:///{}.sqlite'.format(db_name))

    Tag.__table__.drop(engine)
    EventTag.__table__.drop(engine)
    Category.__table__.drop(engine)
    Event.__table__.drop(engine)


def get_session(db_name=_DEFAULT_DBNAME):
    sessionm = create_database(db_name)
    return sessionm()


def add_event(**kwargs):

    new_event = Event(**kwargs)
