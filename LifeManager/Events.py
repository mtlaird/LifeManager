from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, distinct
from sqlalchemy.orm import relationship, reconstructor

Base = declarative_base()


class BaseMixin(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, autoincrement=True)

    def add_to_db(self, session, commit=True):

        self.custom_pre_add(session)

        if not self.id:
            try:
                session.add(self)
            except Exception:
                raise
            if commit:
                session.commit()

        self.custom_post_add(session)

        return True

    def update_in_db(self, session, commit=True):

        self.custom_update(session)

        if self in session and self.id and self in session.dirty:
            if commit:
                session.commit()
            return True
        return False

    @classmethod
    def select_all(cls, session):

        return session.query(cls).all()

    @classmethod
    def select_some(cls, session, **kwargs):

        return session.query(cls).filter_by(**kwargs).all()

    @classmethod
    def select_one(cls, session, **kwargs):

        return session.query(cls).filter_by(**kwargs).first()

    def custom_pre_add(self, session):
        pass

    def custom_post_add(self, session):
        pass

    def custom_update(self, session):
        pass


class Event(BaseMixin, Base):

    title = Column(String)
    description = Column(String)
    category_id = Column(Integer, ForeignKey('category.id'))
    db_add_time = Column(DateTime, default=datetime.utcnow)

    category = relationship('Category')
    tags = relationship('EventTag')

    def __init__(self, **kwargs):

        for key in ['title', 'description', 'category']:
            if key in kwargs:
                self.__setattr__(key, kwargs.pop(key))

        if 'category' not in kwargs:
            self.category = 'event'

        self.new_tags = []
        if 'tags' in kwargs:
            for tag in kwargs['tags']:
                # noinspection PyTypeChecker
                self.add_tag(sess=None, **tag)

    @classmethod
    def get_titles(cls, session):

        return session.query(distinct(Event.title)).order_by(Event.title).all()

    def get_tags(self, raw=False):

        if not raw:
            tags = {}
            # noinspection PyTypeChecker
            for et in self.tags:
                if et.tag.type not in tags:
                    tags[et.tag.type] = et.tag.value
                elif type(tags[et.tag.type]) != list:
                    tags[et.tag.type] = [tags[et.tag.type], et.tag.value]
                else:
                    tags[et.tag.type].append(et.tag.value)

        else:
            tags = []
            # noinspection PyTypeChecker
            for et in self.tags:
                tags.append({'type': et.tag.type, 'value': et.tag.value})

        return tags

    def add_tag(self, sess, **kwargs):

        # Allow users to send tags as either key-value pairs or dicts with type and value specified
        if len(kwargs) == 1:
            tag_type = kwargs.keys()[0]
            tag_value = kwargs[tag_type]
        elif 'type' not in kwargs or 'value' not in kwargs:
            raise ValueError("Tag definition must contain both 'type' and 'value'")
        else:
            tag_type = kwargs['type']
            tag_value = kwargs['value']

        # If object is not yet in database, add tags to the new_tags list
        if not self.id:
            new_tag = {'type': tag_type, 'value': tag_value}
            if new_tag not in self.new_tags:
                self.new_tags.append(new_tag)
            return True

        tag = Tag.select_one(sess, **kwargs)

        if not tag:
            tag = Tag(**kwargs)
            tag.add_to_db(sess, commit=True)

        if not tag.id:
            raise ValueError("Could not determine tag id.")

        et = EventTag(event_id=self.id, tag_id=tag.id)
        et.add_to_db(sess, commit=True)
        return True

    def get_tag_count(self):

        return len(self.get_tags())

    def custom_pre_add(self, session):

        if not self.category_id:
            cat = Category.select_one(session, name=self.category)
            if not cat:
                raise ValueError("Invalid category name: '{}'".format(self.category))

            self.category_id = cat.id
            self.category = cat

    def custom_post_add(self, session):

        for tag in self.new_tags:

            self.add_tag(session, type=tag['type'], value=tag['value'])

        self.new_tags = []

    def custom_update(self, session):

        # self.add_tag(session, type='_db_update_time', value=datetime.utcnow())
        pass

    def duplicate(self, sess, replacement_tags=None, skip_tags=None):

        if replacement_tags is None:
            replacement_tags = []
        if skip_tags is None:
            skip_tags = []
        if type(self.category) is str:
            fixed_cat = self.category
        else:
            fixed_cat = self.category.name
        # Needs to return a subclass if called as a subclass, so new event uses 'self.__class__'
        new_event = self.__class__(title=self.title, description=self.description, category=fixed_cat)

        self_tags = self.get_tags(raw=True)  # Returns a list of dicts
        for tag in self_tags:
            if tag['type'] in skip_tags:
                pass
            else:
                new_event.add_tag(sess, **tag)

        new_tag_keys = [x['type'] for x in new_event.new_tags]  # Extracts keys from list of dicts

        for key in replacement_tags:

            if key in new_tag_keys:
                # Traverse list of dicts to find keys which match replacement tags, then replace them
                existing_tag_index = [i for i, _ in enumerate(new_event.new_tags) if _['type'] == key][0]
                new_event.new_tags[existing_tag_index] = {'type': key, 'value': replacement_tags[key]}
            else:
                new_event.add_tag(sess, type=key, value=replacement_tags[key])

        return new_event


class Category(BaseMixin, Base):

    name = Column(String)

    def __init__(self, **kwargs):

        self.name = kwargs.pop('name')


class Tag(BaseMixin, Base):

    type = Column(String)
    value = Column(String)

    def __init__(self, **kwargs):

        self.type = kwargs.pop('type')
        self.value = kwargs.pop('value')

    @classmethod
    def get_types(cls, session):

        return session.query(distinct(Tag.type)).order_by(Tag.type).all()

    @classmethod
    def get_tags_by_type(cls, session, tag_type):

        return session.query(distinct(Tag.value)).filter(Tag.type == tag_type).order_by(Tag.value).all()

    @classmethod
    def get_types_count(cls, session):

        return session.query(Tag.type, func.count(Tag.type)).group_by(Tag.type).all()

    @classmethod
    def get_tags_count_by_type(cls, session, tag_type):

        query = "SELECT tag.value AS tag_value, count(event.id) as count FROM tag JOIN eventtag " \
                "ON tag.id = eventtag.tag_id JOIN event ON event.id = eventtag.event_id " \
                "WHERE tag.type = '{}' GROUP BY tag.value".format(tag_type)

        # return session.query(Tag.value, func.count(Tag.value)).filter_by(type=tag_type).group_by(Tag.value).all()
        return session.execute(query).fetchall()


class EventTag(BaseMixin, Base):

    event_id = Column(Integer, ForeignKey('event.id'))
    tag_id = Column(Integer, ForeignKey('tag.id'))

    tag = relationship('Tag')

    def __init__(self, **kwargs):

        self.event_id = kwargs.pop('event_id')
        self.tag_id = kwargs.pop('tag_id')


class Timeframe(Tag):
    __tablename__ = 'tag'
    valid_types = ['Date', 'Datetime', 'Timestamp', 'Day_part']

    def __init__(self, **kwargs):

        if kwargs.pop('type') not in self.valid_types:
            raise ValueError
        super(Tag, self).__init__(**kwargs)


class Task(Event):
    __tablename__ = 'event'

    def __init__(self, **kwargs):
        super(Task, self).__init__(**kwargs)

        self.category = 'task'


class Action(Event):
    __tablename__ = 'event'

    def __init__(self, **kwargs):
        super(Action, self).__init__(**kwargs)

        self.category = 'action'
        if 'time' in kwargs and type(kwargs['time']) in (str, unicode) and kwargs['time']:
            self.time = kwargs['time']
        else:
            self.time = datetime.now().strftime("%Y-%m-%d")
        self.new_tags.append({'type': 'Date', 'value': self.time})

    @reconstructor
    def init_on_load(self):
        if 'Date' in self.get_tags():
            self.time = self.get_tags()['Date']
        elif 'date' in self.get_tags():
            self.time = self.get_tags()['date']
        else:
            self.time = None

    @classmethod
    def select_all(cls, session):

        return session.query(cls).join(Action.category).filter_by(name='action').all()

    @classmethod
    def select_some_by_tag(cls, session, tag_type, tag_value):

        return session.query(cls).join(Action.category).filter_by(name='action').join(Action.tags).join(EventTag.tag).\
            filter_by(type=tag_type, value=tag_value)

    def to_json(self):

        return {'id': self.id, 'time': self.time, 'title': self.title, 'description': self.description,
                'tags': self.get_tags()}


def get_events_by_tag(session, tag):

    ret = []
    events = Event.select_all(session)

    for e in events:
        e_tags = e.get_tags()
        if tag['type'] in e_tags:
            if tag['value'] in e_tags[tag['type']]:
                ret.append(e)

    return ret


def get_events_by_category(session, category):

    cat = Category.select_one(session, name=category)

    return Event.select_some(session, category_id=cat.id)
