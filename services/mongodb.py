from pymongo import MongoClient


class MongoDbService(object):
    def __init__(self, connection: str):
        self._connection = connection
        self._client = self._auth()

    @classmethod
    def create_from_connection(cls, connection: str) -> 'MongoDbService':
        return MongoDbService(connection=connection)

    def _auth(self):
        return MongoClient(self._connection, wTimeoutMS=0)

    def get_database(self, name: str):
        return getattr(self._client, name)

    @staticmethod
    def get_collection(database, name: str):
        return getattr(database, name)
