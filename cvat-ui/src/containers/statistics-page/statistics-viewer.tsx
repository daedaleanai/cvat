import React from 'react';
import {
    Col,
    Row,
    Tag,
    Spin,
    Table,
    Tooltip,
    notification,
} from 'antd';
import Text from 'antd/lib/typography/Text';

import getCore from 'cvat-core';

const cvat = getCore();


function StatisticsViewer({ startDate, endDate }) {
    return (
        <StatisticsLoader startDate={startDate} endDate={endDate}>
            {({ data, loading}) => {
                if (loading) return <Spin size='large' className='cvat-spinner' />;
                if (!data) return <Text strong>Cannot load statistics</Text>;
                return <StatisticsTable data={data}/>;
            }}
        </StatisticsLoader>
    );
}

function StatisticsLoader({ startDate, endDate, children }) {
    const [loading, setLoading] = React.useState(false);
    const [data, setData] = React.useState(null);

    React.useEffect(() => {
        let isUpdateRelevant = true;
        setLoading(true);
        cvat.server.getStatistics(startDate, endDate)
            .then(responseData => {
                if (isUpdateRelevant) {
                    setData(responseData);
                }
            })
            .catch((error) => {
                notification.error({
                    message: 'Error while getting statistics',
                    description: error.toString(),
                });
            })
            .finally(() => {
                setLoading(false);
            });
        return () => { isUpdateRelevant = false; };
    }, [startDate, endDate]);

    return children({ data, loading });
}

function StatisticsTable({ data }) {
    const taskNameFilters = React.useMemo(() => getFilters(data, (e) => e.task_name), [data]);
    const taskTypeFilters = React.useMemo(() => getFilters(data, (e) => e.task_type), [data]);
    const AssigneeFilters = React.useMemo(() => getFilters(data, (e) => e.assignee), [data]);
    const columns = [
        {
            title: 'Sequence',
            dataIndex: 'sequence_name',
            defaultSortOrder: 'descend',
            sortDirections: ['descend', 'ascend'],
            sorter: (a, b) => a.sequence_name.localeCompare(b.sequence_name),
            render: (sequenceName, entry) => (
                <Tooltip title={`job-id: ${entry.job_id}`} >
                    {sequenceName}
                </Tooltip>
            ),
        },
        {
            title: 'Task',
            dataIndex: 'task_name',
            sortDirections: ['descend', 'ascend'],
            sorter: (a, b) => a.task_name.localeCompare(b.task_name),
            filters: taskNameFilters,
            onFilter: (value, record) => record.task_name === value,
            render: (taskName, entry) => (
                <Tooltip title={`id: ${entry.task_id}`} >
                    {taskName}
                </Tooltip>
            ),
        },
        {
            title: 'Task type',
            dataIndex: 'task_type',
            filters: taskTypeFilters,
            onFilter: (value, record) => record.task_type === value,
        },
        {
            title: 'Assignee',
            dataIndex: 'assignee',
            sortDirections: ['descend', 'ascend'],
            sorter: (a, b) => a.assignee.localeCompare(b.assignee),
            filters: AssigneeFilters,
            onFilter: (value, record) => record.assignee === value,
            render: (assignee) => (
                <Tag color="blue">
                    {assignee}
                </Tag>
            ),
        },
        {
            title: 'Frames',
            dataIndex: 'frame_count',
            sortDirections: ['descend', 'ascend'],
            sorter: (a, b) => a.frame_count - b.frame_count,
        },
        {
            title: 'Objects',
            dataIndex: 'object_count',
            sortDirections: ['descend', 'ascend'],
            sorter: (a, b) => a.object_count - b.object_count,
        },
        {
            title: 'Time spent',
            dataIndex: 'time_spent_seconds',
            sortDirections: ['descend', 'ascend'],
            sorter: (a, b) => a.time_spent_seconds - b.time_spent_seconds,
            render: (seconds) => formatDuration(seconds),
        },
    ];

    return (
        <Table
            className='cvat-task-jobs-table'
            columns={columns}
            dataSource={data}
            pagination={false}
            footer={(data) => {
                const totalFrames = data.reduce((acc, record) => acc + record.frame_count, 0);
                const totalObjects = data.reduce((acc, record) => acc + record.object_count, 0);
                const totalTimeSpent = data.reduce((acc, record) => acc + record.time_spent_seconds, 0);
                return (
                    <Row>
                        <Col span={3}>
                            <Text strong>Totals:</Text>
                        </Col>
                        <Col span={4}>
                            <Text>frames: </Text><Text strong>{totalFrames}</Text>
                        </Col>
                        <Col span={4}>
                            <Text>objects: </Text><Text strong>{totalObjects}</Text>
                        </Col>
                        <Col span={6}>
                            <Text>time spent: </Text><Text strong>{formatDuration(totalTimeSpent)}</Text>
                        </Col >
                    </Row>
                );
            }}
        />
    );
}

function getFilters(items, mapper) {
    const values = items.map(mapper);
    const uniqueValues = [...new Set(values)];
    return uniqueValues.map(value => ({ text: value + '', value }));
}

function formatDuration(seconds) {
    let minutes, hours, days;
    [minutes, seconds] = divmod(seconds, 60);
    [hours, minutes] = divmod(minutes, 60);
    [days, hours] = divmod(hours, 24);
    const daysPrefix = (days > 0) ? `${days} days, ` : "";
    return `${daysPrefix}${zeroPad(hours, 2)}:${zeroPad(minutes, 2)}`;
}

function divmod(dividend, divisor) {
    const quotient = Math.floor(dividend/divisor);
    const remainder = dividend % divisor;
    return [quotient, remainder];
}

function zeroPad(value, width) {
    const strValue = value + '';
    return strValue.padStart(width, '0');
}

export default StatisticsViewer;
