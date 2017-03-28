from sqlalchemy import (
    Column, MetaData, Table, Integer, String, Text, ForeignKey,
    UniqueConstraint, create_engine
)

metadata = MetaData()

foo = Table(
    'foo', metadata,
    Column(
        'id', Integer, nullable=False, primary_key=True, autoincrement=True
    ), Column('name', String(256), nullable=False)
)

bar = Table(
    'bar',
    metadata,
    Column(
        'id', Integer, nullable=False, primary_key=True, autoincrement=True
    ),
    Column('foo_id', ForeignKey(foo.c.id, ondelete='CASCADE'), nullable=False),
    Column('name', String(256), nullable=False),
)

wumbo = Table(
    'wumo',
    metadata,
    Column(
        'id', Integer, nullable=False, primary_key=True, autoincrement=True
    ),
    Column('foo_id', ForeignKey(foo.c.id, ondelete='CASCADE'), nullable=False),
    Column('bar_id', ForeignKey(bar.c.id, ondelete='CASCADE'), nullable=False),
    Column('name', String(256), nullable=False),
    Column('timestamp', Integer, nullable=False),
    Column('result', String(256), nullable=False),
)

bar_tags = Table(
    'bar_tags',
    metadata,
    Column(
        'id', Integer, nullable=False, primary_key=True, autoincrement=True
    ),
    Column('bar_id', Integer, nullable=False),
    Column('tag_id', Integer, nullable=False),
)

wumbo_tags_table = Table(
    'wumbo_tags',
    metadata,
    Column(
        'id', Integer, nullable=False, primary_key=True, autoincrement=True
    ),
    Column('wumbo_id', Integer, nullable=False),
    Column('tag_id', Integer, nullable=False),
)

tags = Table(
    'tags', metadata,
    Column(
        'id', Integer, nullable=False, primary_key=True, autoincrement=True
    ),
    Column('key', Text, nullable=False),
    Column('value', Text, nullable=False), UniqueConstraint('key', 'value')
)


def connect():
    e = create_engine('sqlite://')
    metadata.create_all(e)
    return e
