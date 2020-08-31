// Copyright (C) 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT

import './styles.scss';
import React from 'react';
import { RouteComponentProps } from 'react-router';
import { withRouter } from 'react-router-dom';

import {
    Col,
    Row,
    Spin,
    Result,
} from 'antd';

import DetailsContainer from 'containers/task-page/details';
import JobListContainer from 'containers/task-page/job-list';
import ValidationReportComponent from 'components/task-page/validation-report';
import ModelRunnerModalContainer from 'containers/model-runner-dialog/model-runner-dialog';
import { Task } from 'reducers/interfaces';
import TopBarComponent from './top-bar';

interface TaskPageComponentProps {
    task: Task | null | undefined;
    fetching: boolean;
    deleteActivity: boolean | null;
    installedGit: boolean;
    getTask: () => void;
}

type Props = TaskPageComponentProps & RouteComponentProps<{id: string}>;

class TaskPageComponent extends React.PureComponent<Props> {
    public constructor(props: Props) {
        super(props);

        const { me } = this.props;
        this.state = {
            // By default show only user's own jobs for annotators, show all jobs for admins
            onlyMine: me.isAnnotator,
        };
    }

    public componentDidUpdate(): void {
        const {
            deleteActivity,
            history,
        } = this.props;

        if (deleteActivity) {
            history.replace('/tasks');
        }
    }

    public render(): JSX.Element {
        const {
            me,
            task,
            fetching,
            getTask,
        } = this.props;
        const { onlyMine } = this.state;

        if (task === null) {
            if (!fetching) {
                getTask();
            }

            return (
                <Spin size='large' className='cvat-spinner' />
            );
        }

        if (typeof (task) === 'undefined') {
            return (
                <Result
                    className='cvat-not-found'
                    status='404'
                    title='Sorry, but this task was not found'
                    subTitle='Please, be sure information you tried to get exist and you have access'
                />
            );
        }

        const mineJobs = onlyMine ? task.instance.jobs.filter(j => (j.assignee || {}).id === me.id).map(j => j.id) : null;

        return (
            <>
                <Row type='flex' justify='center' align='top' className='cvat-task-details-wrapper'>
                    <Col md={22} lg={18} xl={16} xxl={14}>
                        <TopBarComponent
                            taskInstance={(task as Task).instance}
                            setOnlyMine={(v) => this.setState({onlyMine: v})}
                            onlyMine={onlyMine}
                            jobs={mineJobs}
                        />
                        <DetailsContainer task={(task as Task)} />
                        <JobListContainer task={(task as Task)} onlyMine={onlyMine}/>
                        <ValidationReportComponent taskInstance={(task as Task).instance} jobs={mineJobs} />
                    </Col>
                </Row>
                <ModelRunnerModalContainer />
            </>
        );
    }
}

export default withRouter(TaskPageComponent);
