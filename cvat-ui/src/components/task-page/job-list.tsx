// Copyright (C) 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';

import { RouteComponentProps } from 'react-router';
import { withRouter } from 'react-router-dom';

import {
    Row,
    Col,
    Icon,
    Table,
    Button,
    Tooltip,
} from 'antd';

import Text from 'antd/lib/typography/Text';

import moment from 'moment';
import copy from 'copy-to-clipboard';

import getCore from 'cvat-core';
import UserSelector from './user-selector';

const core = getCore();

const baseURL = core.config.backendAPI.slice(0, -7);

interface Props {
    taskInstance: any;
    registeredUsers: any[];
    me: any;
    onlyMine: boolean;
    onJobUpdate(jobInstance: any): void;
}

function JobListComponent(props: Props & RouteComponentProps): JSX.Element {
    const {
        taskInstance,
        registeredUsers,
        me,
        onlyMine,
        onJobUpdate,
        history: {
            push,
        },
    } = props;

    const { jobs, id: taskId } = taskInstance;
    const versionColumns = taskInstance.timesAnnotated === 1 ? [] : [{
        title: 'v',
        dataIndex: 'version',
        key: 'version',
        className: 'cvat-text-color',
    }];
    const columns = [{
        title: 'Job',
        dataIndex: 'job',
        key: 'job',
        render: (id: number): JSX.Element => (
            <div>
                <Button type='link' href={`${baseURL}/?id=${id}`}>{`Job #${id}`}</Button>
                |
                <Tooltip title='Beta version of new UI written in React. It is to get
                                acquainted only, we do not recommend use it to annotation
                                process because it lacks of some features and can be unstable.'
                >
                    <Button
                        type='link'
                        onClick={(): void => {
                            push(`/tasks/${taskId}/jobs/${id}`);
                        }}
                    >
                        Try new UI
                    </Button>
                </Tooltip>
            </div>
        ),
    }, {
        title: 'Sequence name',
        dataIndex: 'sequenceName',
        key: 'sequenceName',
        className: 'cvat-text-color',
    },
        ...versionColumns,
    {
        title: 'Frames',
        dataIndex: 'frames',
        key: 'frames',
        className: 'cvat-text-color',
    }, {
        title: 'Status',
        dataIndex: 'status',
        key: 'status',
        render: (status: string): JSX.Element => {
            let progressColor = null;
            if (status === 'completed') {
                progressColor = 'cvat-job-completed-color';
            } else if (status === 'validation') {
                progressColor = 'cvat-job-validation-color';
            } else {
                progressColor = 'cvat-job-annotation-color';
            }

            return (
                <Text strong className={progressColor}>{ status }</Text>
            );
        },
    }, {
        title: 'Started on',
        dataIndex: 'started',
        key: 'started',
        className: 'cvat-text-color',
    }, {
        title: 'Duration',
        dataIndex: 'duration',
        key: 'duration',
        className: 'cvat-text-color',
    }, {
        title: 'Assignee',
        dataIndex: 'assignee',
        key: 'assignee',
        filteredValue: onlyMine ? [me.id] : null,
        onFilter: (value, record) => (record.assignee.assignee || {}).id === value,
        render: (jobInstance: any): JSX.Element => {
            const assignee = jobInstance.assignee ? jobInstance.assignee.username : null;

            return (
                <UserSelector
                    users={registeredUsers}
                    value={assignee}
                    onChange={(value: string): void => {
                        let [userInstance] = [...registeredUsers]
                            .filter((user: any) => user.username === value);

                        if (userInstance === undefined) {
                            userInstance = null;
                        }

                        // eslint-disable-next-line
                        jobInstance.assignee = userInstance;
                        onJobUpdate(jobInstance);
                    }}
                />
            );
        },
    }];

    let completed = 0;
    const data = jobs.reduce((acc: any[], job: any) => {
        if (job.status === 'completed') {
            completed++;
        }

        const created = moment(props.taskInstance.createdDate);

        acc.push({
            key: job.id,
            job: job.id,
            sequenceName: job.sequenceName,
            version: job.version,
            frames: `${job.startFrame}-${job.stopFrame}`,
            status: `${job.status}`,
            started: `${created.format('MMMM Do YYYY HH:MM')}`,
            duration: `${moment.duration(moment(moment.now()).diff(created)).humanize()}`,
            assignee: job,
        });

        return acc;
    }, []);

    const jobsMessage = onlyMine ?
        `${data.filter(r => (r.assignee.assignee || {}).id === me.id).length} mine jobs` :
        `${completed} of ${data.length} jobs`;

    return (
        <div className='task-section-container'>
            <Row type='flex' justify='space-between' align='middle'>
                <Col>
                    <Text className='cvat-text-color cvat-jobs-header'> Jobs </Text>
                    <Tooltip trigger='click' title='Copied to clipboard!'>
                        <Button
                            type='link'
                            onClick={(): void => {
                                let serialized = '';
                                const [latestJob] = [...taskInstance.jobs].reverse();
                                for (const job of taskInstance.jobs) {
                                    serialized += `Job #${job.id}`.padEnd(`${latestJob.id}`.length + 6, ' ');
                                    serialized += `: ${baseURL}/?id=${job.id}`
                                        .padEnd(`${latestJob.id}`.length + baseURL.length + 8, ' ');
                                    serialized += `: [${job.startFrame}-${job.stopFrame}]`
                                        .padEnd(`${latestJob.startFrame}${latestJob.stopFrame}`.length + 5, ' ');

                                    if (job.assignee) {
                                        serialized += `\t assigned to: ${job.assignee.username}`;
                                    }
                                    serialized += '\n';
                                }
                                copy(serialized);
                            }}
                        >
                            <Icon type='copy' theme='twoTone' />
                            Copy
                        </Button>
                    </Tooltip>
                </Col>
                <Col>
                    <Text className='cvat-text-color'>
                        {jobsMessage}
                    </Text>
                </Col>
            </Row>
            <Table
                className='cvat-task-jobs-table'
                columns={columns}
                dataSource={data}
                size='small'
            />
        </div>
    );
}

export default withRouter(JobListComponent);
