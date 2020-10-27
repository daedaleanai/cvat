import React, { useState } from 'react';
import { connect } from 'react-redux';

import {
    Spin,
    Select,
    notification,
} from 'antd';

import { CombinedState } from 'reducers/interfaces';

interface Props {
    job: any;
}


interface StateToProps {
    users: any[];
}

function mapStateToProps(state: CombinedState): StateToProps {
    return {
        users: state.users.users,
    };
}

function ConcurrentUserSelector(props: Props & StateToProps): JSX.Element {
    const [loading, setLoading] = useState(false);
    const {
        job,
        users,
    } = props;

    const assignee = job.assignee ? job.assignee.id : null;

    const handleChange = (value) => {
        let [userInstance] = users.filter((user) => user.id === value);
        userInstance = userInstance || null;

        const prevAssignee = job.assignee;
        job.assignee = userInstance;
        setLoading(true);
        job.assign().catch((error) => {
            job.assignee = prevAssignee;
            if (error.code === 409) {
                notification.error({
                    message: 'Cannot assign the job',
                    description: "One of sequence's jobs has been picked up by another annotator. " +
                        "Please, refresh the page to see the updated version",
                });
            } else {
                console.log(error);
            }
        }).finally(() => {
            setLoading(false);
        });
    };

    return (
        <Spin spinning={loading} size='small'>
            <Select
                value={assignee || '0'}
                size='small'
                showSearch
                className='cvat-user-selector'
                onChange={handleChange}
            >
                <Select.Option key='-1' value='0'>—</Select.Option>
                { users.map((user) => (
                    <Select.Option key={user.id} value={user.id}>
                        {user.username}
                    </Select.Option>
                ))}
            </Select>
        </Spin>
    );
}


export default connect(mapStateToProps)(ConcurrentUserSelector);
