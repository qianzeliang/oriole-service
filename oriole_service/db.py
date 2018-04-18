#
#                __   _,--="=--,_   __
#               /  \."    .-.    "./  \
#              /  ,/  _   : :   _  \/` \
#              \  `| /o\  :_:  /o\ |\__/
#               `-'| :="~` _ `~"=: |
#                  \`     (_)     `/
#           .-"-.   \      |      /   .-"-.
#    .-----{     }--|  /,.-'-.,\  |--{     }-----.
#     )    (_)_)_)  \_/`~-===-~`\_/  (_(_(_)    (
#    (                                           )
#     )                 Oriole-DB               (
#    (                  Eric.Zhou                )
#    '-------------------------------------------'
#

from weakref import WeakKeyDictionary

from nameko.extensions import DependencyProvider

from oriole.db import *

MyBase = declarative_base()


class Base(MyBase):
    __abstract__ = True

    def __init__(self, **kwargs):
        for attr in self.__mapper__.column_attrs:
            key = attr.key
            if key in kwargs:
                continue

            val = attr.columns[0].default
            if val and not callable(val.arg):
                kwargs[key] = val.arg

        super().__init__(**kwargs)


class Db(DependencyProvider):
    def __init__(self, Base, uri="database"):
        self.base = Base
        self.uri = uri
        self.dbs = WeakKeyDictionary()

    def setup(self):
        self.bind = get_engine(self.container.config.get(self.uri))
        self.base.metadata.create_all(self.bind)

    def get_dependency(self, worker_ctx):
        session = get_session(self.bind)
        self.dbs[worker_ctx] = session

        return session

    def worker_teardown(self, worker_ctx):
        session = self.dbs.pop(worker_ctx)
        session.close()


class Rs(DependencyProvider):
    def __init__(self, uri="datasets"):
        self.uri = uri

    def setup(self):
        self.rs = get_redis(self.container.config.get(self.uri))

    def get_dependency(self, worker_ctx):
        return self.rs
