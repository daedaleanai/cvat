// Copyright (C) 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';

import {
    Row,
    Col,
    Button,
    Dropdown,
    Tooltip,
    Switch,
    Icon,
} from 'antd';

import Text from 'antd/lib/typography/Text';

import ActionsMenuContainer from 'containers/actions-menu/actions-menu';
import { MenuIcon } from 'icons';

interface DetailsComponentProps {
    taskInstance: any;
    onlyMine: boolean;
    setOnlyMine(value: boolean): void;
    jobs: any[] | null;
    allowLoad: boolean;
}

export default function DetailsComponent(props: DetailsComponentProps): JSX.Element {
    const { taskInstance, onlyMine, setOnlyMine, jobs, allowLoad } = props;
    const { id } = taskInstance;

    return (
        <Row className='cvat-task-top-bar' type='flex' justify='end' align='middle'>
            <Col>
                <Text className='cvat-title'>{`Task details #${id}`}</Text>
            </Col>
            <Col>
                <Tooltip title='Show, dump, upload, validate only my jobs'>
                    <Switch checked={onlyMine} onChange={setOnlyMine} />
                </Tooltip>
            </Col>
            <Col offset={1}>
                <Dropdown overlay={
                    (
                        <ActionsMenuContainer
                            taskInstance={taskInstance}
                            jobs={jobs}
                            allowLoad={allowLoad}
                        />
                    )
                }
                >
                    <Button size='large'>
                        <Text className='cvat-text-color'>Actions</Text>
                        <Icon className='cvat-menu-icon' component={MenuIcon} />
                    </Button>
                </Dropdown>
            </Col>
        </Row>
    );
}
