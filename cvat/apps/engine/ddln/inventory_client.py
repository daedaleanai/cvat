import datetime as dt

from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build

from cvat.apps.engine.log import slogger
from cvat.apps.engine.utils import singleton


@singleton
def create_inventory_client():
    # googleapiclient.discovery.build() makes http request to fetch coreapi schema
    # and build object-oriented api based on the schema.
    # Get rid of those extra http requests by turning `InventoryClient` into singleton

    spreadsheet_id = settings.INVENTORY_SPREADSHEET_ID
    credentials_file = settings.INVENTORY_CREDENTIALS_FILENAME
    if spreadsheet_id is None or credentials_file is None:
        slogger.glob.warning("Using DummyInventoryClient as inventory configuration is not properly set")
        return DummyInventoryClient()
    return InventoryClient(spreadsheet_id, credentials_file)


class InventoryClient:
    def __init__(self, spreadsheet_id, credentials_file, scopes=None):
        if scopes is None:
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = service_account.Credentials.from_service_account_file(credentials_file, scopes=scopes)
        self._service = build('sheets', 'v4', credentials=credentials)
        self.spreadsheet_id = spreadsheet_id

    def record_sequence_completion(self, sequence_name: str, task_name: str, annotator: str, completion_date: dt.date):
        completion_date = "{:%d.%m.%Y}".format(completion_date)
        row = [sequence_name, 'image', 'CVAT', task_name, completion_date, annotator]
        request = self._service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range='A1:I1',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={
                'values': [row]
            }
        )
        response_data = request.execute()
        return response_data['updates']['updatedRange']


class DummyInventoryClient:
    def record_sequence_completion(self, sequence_name: str, task_name: str, annotator: str, completion_date: dt.date):
        return ''
