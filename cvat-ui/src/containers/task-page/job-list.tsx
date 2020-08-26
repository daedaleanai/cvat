// Copyright (C) 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';
import { connect } from 'react-redux';

import JobListComponent from 'components/task-page/job-list';
import { updateJobAsync } from 'actions/tasks-actions';
import {
    Task,
    CombinedState,
} from 'reducers/interfaces';

interface OwnProps {
    task: Task;
}

interface StateToProps {
    registeredUsers: any[];
    me: any;
}

interface DispatchToProps {
    onJobUpdate(jobInstance: any): void;
}

function mapStateToProps(state: CombinedState): StateToProps {
    return {
        registeredUsers: state.users.users,
        me: state.auth.user,
    };
}

function mapDispatchToProps(dispatch: any): DispatchToProps {
    return {
        onJobUpdate: (jobInstance: any): void => dispatch(updateJobAsync(jobInstance)),
    };
}

function TaskPageContainer(props: StateToProps & DispatchToProps & OwnProps): JSX.Element {
    const {
        task,
        me,
        registeredUsers,
        onJobUpdate,
    } = props;

    return (
        <JobListComponent
            taskInstance={task.instance}
            me={me}
            registeredUsers={registeredUsers}
            onJobUpdate={onJobUpdate}
        />
    );
}

export default connect(
    mapStateToProps,
    mapDispatchToProps,
)(TaskPageContainer);
