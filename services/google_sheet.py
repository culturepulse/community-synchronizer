import pygsheets
from pygsheets import Spreadsheet
from pygsheets.client import Client


class GoogleSheetService(object):
    def __init__(self, scope: str):
        self._scope = scope
        self._client = self._auth()

    @classmethod
    def create_from_scope(cls, scope: str) -> 'GoogleSheetService':
        return GoogleSheetService(scope=scope)

    @staticmethod
    def _auth() -> Client:
        client = pygsheets.authorize(service_file='credentials.json')
        return client

    def get_sheet(self, spreadsheet_id: str) -> Spreadsheet:
        sheet = self._client.open_by_key(key=spreadsheet_id)
        print(f"Opened spreadsheet with id:{sheet.id} and url:{sheet.url}")

        return sheet
