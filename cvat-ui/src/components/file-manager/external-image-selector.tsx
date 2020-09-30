import React, { useState } from 'react';
import {
    Icon,
    Spin,
    Upload,
} from 'antd';
import Text from 'antd/lib/typography/Text';

const csvHeader = ["sequenceName", "recordingName", "startFrame", "endFrame", "cameraIndex", "targetName", "targetType"];

const ExternalImagesSelector = ({ value, onChange }) => {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    return (
        <Spin spinning={loading}>
            <Upload.Dragger
                accept=".csv"
                listType='text'
                fileList={file ? [file] : []}
                showUploadList={{
                    showRemoveIcon: false,
                }}
                beforeUpload={(file) => {
                    setFile(file);
                    setLoading(true);
                    loadData(file).then((data) => {
                        onChange(data);
                    }).catch((error) => {
                        console.error(error);
                    }).finally(() => {
                        setLoading(false);
                    });
                    return false;
                }}
            >
                <p className='ant-upload-drag-icon'>
                    <Icon type="cloud-upload" />
                </p>
                <p className='ant-upload-text'>Click or drag file to this area</p>
                <p className='ant-upload-hint'>
                    Upload a csv file containing sequences data
                </p>
            </Upload.Dragger>
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

async function loadData(file) {
    const csvFileContent = await readTextFile(file);
    const sequences = parseCsv(csvFileContent, csvHeader);
    const cachedFetchRecording = cached(fetchRecordingData);
    const recordings = await Promise.all(sequences.map(s => cachedFetchRecording(s.recordingName)));
    return sequences.map((s, i) => joinData(s, recordings[i][Number(s.cameraIndex)]));
}

function readTextFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = event => { resolve(event.target.result) };
        reader.onerror = event => { reject(reader.error) };
        reader.readAsText(file);
    });
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
    ;
}

function processRecordingData(data) {
    return data.record.cam.map(item => {
        const { width, height } = item.params;
        const frames = item.abs_timestamp_ns.map(padFrameName);
        const indexByFrame = {};
        item.abs_timestamp_ns.forEach((f, i) => indexByFrame[f] = i);
        return { width, height, frames, indexByFrame };
    })
}

function padFrameName(name) {
    return name.padStart(20, '0');
}

function joinData(sequenceData, recordingData) {
    const { sequenceName, recordingName, cameraIndex } = sequenceData;
    const { indexByFrame, width, height } = recordingData;
    const frameNames = recordingData.frames.slice(
        indexByFrame[sequenceData.startFrame],
        indexByFrame[sequenceData.endFrame] + 1
    );
    const frames = frameNames.map((f) => ({
        path: `/.upload/${sequenceName}/cam${cameraIndex}/data/${f}.jpg`,
        url: `/${recordingName}/cam${cameraIndex}/${f}.jpg`,
    }));
    return { sequence_name: sequenceName, camera_index: cameraIndex, width, height, frames };
}

export default ExternalImagesSelector;
