import datetime as dt
from typing import List, Tuple

from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build

from cvat.apps.engine.log import slogger
from cvat.apps.engine.utils import singleton


def record_sequence_completion(job_id, sequence_name, task_name, annotator, annotation_date=None):
    if annotation_date is None:
        annotation_date = dt.date.today()
    try:
        client = create_inventory_client()
        affected_cells = client.record_sequence_completion(sequence_name, task_name, annotator, annotation_date)
        slogger.glob.info("Job %s completed. Made a record in inventory file: '%s'", job_id, affected_cells)
    except Exception:
        slogger.glob.exception("Error while making the job completion record")


def record_task_creation(task, segments):
    if not segments:
        return
    try:
        pairs = [(seq_name, (assignee.username if assignee else '')) for seq_name, _, _, _, assignee in segments]
        client = create_inventory_client()
        affected_cells = client.record_task_creation(task.name, pairs)
        slogger.glob.info("Task %s has been created. Made a record in inventory file: '%s'", task.id, affected_cells)
    except Exception:
        slogger.glob.exception("Error while making the task creation record")



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
        row_index = self._get_row_index(sequence_name, task_name)
        if row_index == -1:
            raise ValueError("sequence {!r} for task {!r} is not found.".format(sequence_name, task_name))
        completion_date = "{:%d.%m.%Y}".format(completion_date)
        row = [annotator, completion_date]
        request = self._service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range='E{}:F{}'.format(row_index, row_index),
            valueInputOption='USER_ENTERED',
            body={
                'values': [row]
            }
        )
        response_data = request.execute()
        return response_data['updatedRange']

    def record_task_creation(self, task_name: str, sequence_annotator_pairs: List[Tuple[str, str]]):
        if not sequence_annotator_pairs:
            return ''

        # Do not write new rows if the file already has rows for the given sequences
        index = self._get_row_index(sequence_annotator_pairs[0][0], task_name)
        if index != -1:
            return ''

        rows = [
            [sequence_name, task_name, 'image', 'CVAT', annotator]
            for sequence_name, annotator in sequence_annotator_pairs
        ]
        request = self._service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range='A1:I1',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={
                'values': rows
            }
        )
        response_data = request.execute()
        return response_data['updates']['updatedRange']

    def _get_row_index(self, sequence_name: str, task_name: str):
        request = self._service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A1:B',
        )
        response_data = request.execute()
        for i, (seq, task) in enumerate(response_data['values'], start=1):
            if seq == sequence_name and task == task_name:
                return i
        return -1


class DummyInventoryClient:
    def record_sequence_completion(self, sequence_name: str, task_name: str, annotator: str, completion_date: dt.date):
        return ''

    def record_task_creation(self, task_name: str, sequence_annotator_pairs: List[Tuple[str, str]]):
        return ''
