import dataclasses
from dataclasses import asdict
from datetime import datetime
from typing import List, Union
from zoneinfo import ZoneInfo

import pygsheets
from pygsheets import Cell

from conf import settings
from services.google_sheet_client import GoogleSheetClient
from services.mongodb_scraper import MongoDbScraper


class GoogleSheetWriter:
    def __init__(self):
        google_sheet_service = GoogleSheetClient.create_from_scope(scope=settings.GOOGLE_SCOPE)
        self._spreadsheet = google_sheet_service.get_sheet(settings.GOOGLE_SPREADSHEET_ID)

    def get_communities(self) -> list:
        sheet = self._spreadsheet.worksheet_by_title('Communities, Groups, Subgroups (Coda)')
        communities = list(dict.fromkeys(sheet.get_col(col=1, include_tailing_empty=False)[1:]))

        return communities

    def write_data(self, all_data: List[Union[MongoDbScraper.CommunityTitleRow, MongoDbScraper.CommunityContentRow]]):
        time_now = datetime.now(tz=ZoneInfo('Europe/Bratislava')).strftime("%Y-%m-%d %H:%M:%S")
        sheet = self._spreadsheet.worksheet_by_title('Communities scraped data')
        sheet.clear()

        data_to_insert = []
        for item in all_data:
            data_to_insert.append([getattr(item, field.name) for field in dataclasses.fields(item)])

        end_column = chr(len(asdict(all_data[0]))+65)
        end_row = len(all_data)+1

        sheet.update_values(crange=f'A1:{end_column}{end_row}', values=data_to_insert)
        sheet.sort_range('A2', f'{end_column}{end_row}', basecolumnindex=0, sortorder='ASCENDING')

        sheet.update_value('K1', "Scraped at:")
        sheet.update_value('L1', time_now)

        model_cell = Cell('A1')
        model_cell.set_text_format('bold', True)
        model_cell.set_text_format('fontSize', 12)

        title_range = pygsheets.DataRange(start='A1', end='J1', worksheet=sheet)
        title_range.apply_format(model_cell)
