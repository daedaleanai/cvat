import os

import requests
from datetime import datetime

from cvat.apps.engine.ddln.tasks import guess_task_type
from cvat.apps.engine.models import Job, Segment

METRICS_HOST = "http://{}:{}/api/console/proxy?path=_search&method=POST".format(
    os.getenv('DJANGO_LOG_VIEWER_HOST'),
    os.getenv('DJANGO_LOG_VIEWER_PORT')
)


def get_statistics(start, end):
    data = get_analytics_data(start, end)
    job_ids = [e['job_id'] for e in data]
    db_data = get_db_data(job_ids)
    db_record_by_job_id = {e['job_id']: e for e in db_data}
    for e in data:
        e.update(db_record_by_job_id.get(e['job_id'], {}))
    return data


def get_db_data(job_ids):
    job_segment_id_pair = [(job.id, job.segment.id) for job in Job.objects.filter(id__in=job_ids)]
    segment_ids = [segment_id for job_id, segment_id in job_segment_id_pair]
    segments = (
        Segment.objects
        .filter(id__in=segment_ids)
        .select_related("task")
        .prefetch_related("task__label_set")
        .with_sequence_name()
    )
    segment_data_by_id = {}
    task_type_by_id = {}
    for segment in segments:
        task = segment.task
        entry = dict(sequence_name=segment.sequence_name, task_id=task.id, task_name=task.name)
        if task.id not in task_type_by_id:
            task_type = guess_task_type(task)
            if task_type is None:
                task_type = "unknown"
            elif task_type == "vls-lines":
                task_type = "vls"
            task_type_by_id[task.id] = task_type
        entry['task_type'] = task_type_by_id[task.id]
        segment_data_by_id[segment.id] = entry

    result = []
    for job_id, segment_id in job_segment_id_pair:
        entry = dict(job_id=job_id)
        entry.update(segment_data_by_id[segment_id])
        result.append(entry)
    return result


def get_analytics_data(start, end):
    finish_data = _get_jobs_finish_data(start, end)
    start_data = _get_jobs_start_data(start, end)
    start_record_by_job_id = {e['job_id']: e for e in start_data}
    result = []
    for finish_entry in finish_data:
        entry = finish_entry.copy()
        finish_time = entry.pop("finish_time")
        entry['finish_time'] = finish_time.isoformat()
        entry['start_time'] = ''
        entry['time_spent_seconds'] = None
        start_entry = start_record_by_job_id.get(entry['job_id'])
        if start_entry:
            entry['time_spent_seconds'] = int((finish_time - start_entry['start_time']).total_seconds())
            entry['start_time'] = start_entry['start_time'].isoformat()
            entry['object_count'] -= start_entry['object_count']
        result.append(entry)
    return result


def _get_jobs_finish_data(start, end):
    data = {
        "aggs": {
            "job_finish": {
                "terms": {
                    "field": "job_id",
                    "size": 999,
                    "order": {
                        "_count": "desc"
                    }
                },
                "aggs": {
                    "last_entry": {
                        "top_hits": {
                            "size": 1,
                            "sort": [
                                {
                                    "@timestamp": {
                                        "order": "desc",
                                        "unmapped_type": "date"
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        },
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": _to_unix_milliseconds(start),
                                "lte": _to_unix_milliseconds(end),
                                "format": "epoch_millis"
                            }
                        }
                    },
                    {
                        "match_phrase": {
                            "event": {
                                "query": "Send task info"
                            }
                        }
                    }
                ],
                "filter": [],
                "should": [],
                "must_not": []
            }
        }
    }
    headers = {"kbn-version": "6.4.0"}
    response = requests.post(METRICS_HOST, json=data, headers=headers)
    json = response.json()

    result = []
    for row in json['aggregations']['job_finish']['buckets']:
        row_data = row['last_entry']['hits']['hits'][0]['_source']
        entry = {
            "job_id": row_data['job_id'],
            "assignee": row_data['username'],
            "frame_count": row_data['frame count'],
            "object_count": row_data['object count'],
            "finish_time": _parse_time(row_data['@timestamp']),
        }
        result.append(entry)
    return result


def _get_jobs_start_data(start, end):
    data = {
        "aggs": {
            "job_start": {
                "terms": {
                    "field": "job_id",
                    "size": 999,
                    "order": {
                        "_count": "desc"
                    }
                },
                "aggs": {
                    "first_entry": {
                        "top_hits": {
                            "size": 1,
                            "sort": [
                                {
                                    "@timestamp": {
                                        "order": "asc",
                                        "unmapped_type": "date"
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        },
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": _to_unix_milliseconds(start),
                                "lte": _to_unix_milliseconds(end),
                                "format": "epoch_millis"
                            }
                        }
                    },
                    {
                        "match_phrase": {
                            "event": {
                                "query": "Load job"
                            }
                        }
                    }
                ],
                "filter": [],
                "should": [],
                "must_not": []
            }
        }
    }
    headers = {"kbn-version": "6.4.0"}
    response = requests.post(METRICS_HOST, json=data, headers=headers)
    json = response.json()

    result = []
    for row in json['aggregations']['job_start']['buckets']:
        row_data = row['first_entry']['hits']['hits'][0]['_source']
        entry = {
            "job_id": row_data['job_id'],
            "object_count": row_data['object count'],
            "start_time": _parse_time(row_data['@timestamp']),
        }
        result.append(entry)
    return result


def _parse_time(input):
    return datetime.strptime(input, '%Y-%m-%dT%H:%M:%S.%fZ')


def _to_unix_milliseconds(datetime):
    return int(datetime.timestamp() * 1000)
