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

    def _auth(self) -> Client:
        client = pygsheets.authorize(client_secret='credentials.json')
        return client

    def get_sheet(self, name: str) -> Spreadsheet:
        try:
            sheet = self._client.open(name)
            print(f"Opened spreadsheet with id:{sheet.id} and url:{sheet.url}")
        except pygsheets.SpreadsheetNotFound:
            # Can't find it and so create it
            res = self._client.sheet.create(name)
            sheet_id = res['spreadsheetId']
            sheet = self._client.open_by_key(sheet_id)
            print(f"Created spreadsheet with id:{sheet.id} and url:{sheet.url}")

        return sheet
