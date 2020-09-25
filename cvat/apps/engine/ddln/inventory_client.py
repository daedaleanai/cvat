import datetime as dt

from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build

from cvat.apps.engine.log import slogger
from cvat.apps.engine.utils import singleton, find_range


def record_sequence_completion(job_id, sequence_name, version, task_name, annotator, annotation_date=None):
    if annotation_date is None:
        annotation_date = dt.date.today()
    try:
        client = create_inventory_client()
        affected_cells = client.record_sequence_completion(sequence_name, version, task_name, annotator, annotation_date)
        slogger.glob.info("Job %s completed. Made a record in inventory file: '%s'", job_id, affected_cells)
    except Exception:
        slogger.glob.exception("Error while making the job completion record")


def record_task_creation(task, segments):
    if not segments:
        return
    try:
        data = []
        for seq_name, _, _, _, assignees in segments:
            for version, assignee in enumerate(assignees):
                data.append((seq_name, version, (assignee.username if assignee else '')))
        client = create_inventory_client()
        affected_cells = client.record_task_creation(task.name, data)
        slogger.glob.info("Task %s has been created. Made a record in inventory file: '%s'", task.id, affected_cells)
    except Exception:
        slogger.glob.exception("Error while making the task creation record")


def record_task_validation(task, validator, validation_date=None):
    if validation_date is None:
        validation_date = dt.date.today()
    try:
        client = create_inventory_client()
        affected_cells = client.record_task_validation(task.name, validator, validation_date)
        slogger.glob.info("Task %s validated. Made a record in inventory file: '%s'", task.id, affected_cells)
    except Exception:
        slogger.glob.exception("Error while making the task validation record")


def record_extra_annotation_creation(task, assignments, version):
    try:
        data = []
        for segment, assignee in assignments:
            data.append((segment.sequence_name, version, (assignee.username if assignee else '')))
        client = create_inventory_client()
        # Ideally, new rows should be inserted next to the existing rows for the task, but
        # it might be not safe to insert rows concurrently, but append should be safe
        # record_task_creation() does what we need, no need for record_extra_annotation_creation()
        affected_cells = client.record_task_creation(task.name, data)
        message = "Extra annotation for task %s has been created. Made a record in inventory file: '%s'"
        slogger.glob.info(message, task.id, affected_cells)
    except Exception:
        slogger.glob.exception("Error while making the extra annotation creation record")


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

    def record_sequence_completion(self, sequence_name, version, task_name, annotator, completion_date):
        row_index = self._get_row_index(sequence_name, version, task_name)
        if row_index == -1:
            raise ValueError("sequence {!r} for task {!r}-v{} is not found.".format(sequence_name, task_name, version))
        completion_date = "{:%d.%m.%Y}".format(completion_date)
        row = [annotator, completion_date]
        request = self._service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range='F{}:G{}'.format(row_index, row_index),
            valueInputOption='USER_ENTERED',
            body={
                'values': [row]
            }
        )
        response_data = request.execute()
        return response_data['updatedRange']

    def record_task_creation(self, task_name, assignment_data):
        if not assignment_data:
            return ''

        # Do not write new rows if the file already has rows for the given sequences
        index = self._get_row_index(assignment_data[0][0], assignment_data[0][1], task_name)
        if index != -1:
            return ''

        rows = [
            [sequence_name, version+1, task_name, 'image', 'CVAT', annotator]
            for sequence_name, version, annotator in assignment_data
        ]
        request = self._service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range='A1:J1',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={
                'values': rows
            }
        )
        response_data = request.execute()
        return response_data['updates']['updatedRange']

    def record_task_validation(self, task_name, validator, validation_date):
        start_row, end_row = self._get_task_range(task_name)
        if end_row < start_row:
            raise ValueError("Records for task {!r} are not found.".format(task_name))
        validation_date = "{:%d.%m.%Y}".format(validation_date)
        rows = [[validator, validation_date] for _ in range(start_row, end_row + 1)]
        request = self._service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range='H{}:I{}'.format(start_row, end_row),
            valueInputOption='USER_ENTERED',
            body={
                'values': rows
            }
        )
        response_data = request.execute()
        return response_data['updatedRange']

    def _get_row_index(self, sequence_name, version, task_name):
        version = str(version + 1)
        request = self._service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A1:C',
        )
        response_data = request.execute()
        for i, row in enumerate(response_data['values'], start=1):
            if len(row) != 3:
                continue
            seq, ver, task = row
            if seq == sequence_name and ver == version and task == task_name:
                return i
        return -1

    def _get_task_range(self, task_name):
        # 1-index, end index is inclusive
        request = self._service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='C1:C',
        )
        response_data = request.execute()
        values = [row[0] if len(row) == 1 else None for row in response_data['values']]
        start_index, end_index = find_range(values, lambda v: v == task_name)
        return start_index + 1, end_index


class DummyInventoryClient:
    def record_sequence_completion(self, sequence_name, version, task_name, annotator, completion_date):
        return ''

    def record_task_creation(self, task_name, assignment_data):
        return ''

    def record_task_validation(self, task_name, validator, validation_date):
        return ''
