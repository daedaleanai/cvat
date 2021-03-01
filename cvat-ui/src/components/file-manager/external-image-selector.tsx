import React, { useState } from 'react';
import {
    Spin,
    Button,
    notification,
} from 'antd';
import Text from 'antd/lib/typography/Text';

import ShareSelector from "./share-selector";

const csvHeader = ["sequenceName", "recordingName", "startFrame", "endFrame", "cameraIndex", "targetName", "targetType"];

const ExternalImagesSelector = ({ value, onChange }) => {
    const [selection, setSelection] = useState([]);
    const [loading, setLoading] = useState(false);

    const onSubmit = () => {
        setLoading(true);
        loadData(selection).then((data) => {
            onChange(data);
        }).catch((error) => {
            notification.error({
                message: 'Error while getting scenarios',
                description: error.toString(),
            });
        }).finally(() => {
            setLoading(false);
        });
    }

    return (
        <Spin spinning={loading}>
            <ShareSelector value={selection} onchange={setSelection} />
            <Button size='large' type='primary' onClick={onSubmit} disabled={selection.length < 1} >
                 Select files
            </Button>
            {
                value.map(item => (
                    <Text className='cvat-text-color'>
                        <br />{item.sequence_name}: {item.frames.length} frames
                    </Text>
                ))
            }
        </Spin>
    );
}

async function loadData(selection) {
    const csvFileContent = await getScenarioFile(selection);
    let sequences = parseCsv(csvFileContent, csvHeader);
    sequences = filterUnique(sequences, (s) => s.sequenceName);
    // In order to get all the necessary data for task creation,
    // have to fetch recording data from records service for each sequence,
    // but making requests for each sequence leads to duplicated requests
    // as multiple sequences belong to the same recording,
    // use caching to de-duplicate requests
    const cachedFetchRecording = cached(fetchRecordingData);
    const recordings = await Promise.all(sequences.map(s => cachedFetchRecording(s.recordingName)));
    return sequences.map((s, i) => joinData(s, recordings[i][Number(s.cameraIndex)]));
}

function filterUnique(array, keyExtractor) {
    const result = [];
    const seen = new Set();
    array.forEach(el => {
        const key = keyExtractor(el);
        if (!seen.has(key)) {
            result.push(el);
        }
        seen.add(key);
    })
    return result;
}

async function getScenarioFile(paths) {
    const query = new URLSearchParams();
    paths.forEach(p => query.append("path", p));
    const response = await fetch(`/api/v1/server/scenario-file?${query}`);
    if (response.status === 200) {
        return response.text();
    } else if (response.status === 406) {
        const data = await response.json();
        const message = `${data.message} Possible choices: ${data.choices.join(", ")}.`;
        throw Error(message);
    } else if (response.status === 404) {
        throw Error("Scenario file not found.");
    } else {
        console.log(response);
        throw Error("Unknown error");
    }
}

function parseCsv(text, header) {
    const lines = text.trim().split(/\r\n|\n/);
    const result = [];
    lines.forEach((line) => {
        const fields = line.split(',');
        const obj = {};
        header.forEach((name, i) => {
            obj[name] = fields[i];
        });
        result.push(obj);
    })
    return result;
}

function cached(fetcher) {
    const cache = {};
    return (...args) => {
        const key = JSON.stringify(args);
        if (key in cache) {
            return cache[key];
        }
        const promise = fetcher(...args);
        cache[key] = promise;
        return promise;
    };
}

function fetchRecordingData(recordingName) {
    const host = process.env.EXTERNAL_STORAGE_HOST;
    const url = `${host}/${recordingName}/record.json?types=cam&interval=0`;
    return fetch(url, {credentials: "include"})
        .then(response => response.json())
        .then(data => processRecordingData(data))
        .catch(error => console.log(error))
    ;
}

function processRecordingData(data) {
    return data.record.cam.map(item => {
        const { width, height } = item.params;
        const sourceFrames = item.abs_timestamp_ns || [];
        const frames = sourceFrames.map(padFrameName);
        return { width, height, frames, sourceFrames };
    });
}

function padFrameName(name) {
    return name.padStart(20, '0');
}

function joinData(sequenceData, recordingData) {
    const { sequenceName, recordingName, cameraIndex, startFrame, endFrame } = sequenceData;
    const { sourceFrames, width, height } = recordingData;
    const startFrameIndex = binarySearch(sourceFrames, startFrame);
    let endFrameIndex = binarySearch(sourceFrames, endFrame);
    if (sourceFrames[endFrameIndex] === endFrame) {
        ++endFrameIndex;
    }
    const frameNames = recordingData.frames.slice(startFrameIndex, endFrameIndex);
    const frames = frameNames.map((f) => ({
        path: `/.upload/${sequenceName}/cam${cameraIndex}/data/${f}.jpg`,
        url: `/${recordingName}/cam${cameraIndex}/${f}.jpg`,
    }));
    return { sequence_name: sequenceName, camera_index: cameraIndex, width, height, frames };
}

function binarySearch(array, value) {
    let left = 0;
    let right = array.length;
    while (left < right) {
        const mid = left + Math.floor((right - left) / 2);
        if (array[mid] < value) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    return left;
}

export default ExternalImagesSelector;
