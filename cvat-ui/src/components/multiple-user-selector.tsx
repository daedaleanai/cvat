import React from 'react';
import { connect } from 'react-redux';

import {
    Select,
} from 'antd';

import { CombinedState } from 'reducers/interfaces';

interface Props {
    value: string[];
    onChange: (users: string[]) => void;
}


interface StateToProps {
    users: any[];
}

function mapStateToProps(state: CombinedState): StateToProps {
    return {
        users: state.users.users,
    };
}

function MultipleUserSelector(props: Props & StateToProps): JSX.Element {
    const {
        users,
        ...rest
    } = props;

    const sortedUsers = [...users].sort((a, b) => a.username.localeCompare(b.username));
    const annotators = sortedUsers.filter(u => u.isAnnotator);
    const others = sortedUsers.filter(u => !u.isAnnotator);

    return (
        <Select mode='multiple' size='large' {...rest}>
            { annotators.map((user): JSX.Element => (
                <Select.Option key={user.id} value={user.id}>
                    {user.username}
                </Select.Option>
            ))}
            {!!others.length && <Select.OptGroup label="Others">
                { others.map((user): JSX.Element => (
                    <Select.Option key={user.id} value={user.id}>
                        {user.username}
                    </Select.Option>
                ))}
            </Select.OptGroup>}
        </Select>
    );
}


export default connect(mapStateToProps)(MultipleUserSelector);
