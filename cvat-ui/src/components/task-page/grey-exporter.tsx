import React, { useState } from 'react';
import { connect } from 'react-redux';
import {
    Row,
    Col,
    Button,
    notification,
} from 'antd';
import Text from 'antd/lib/typography/Text';
import { CombinedState } from "reducers/interfaces";

interface Props {
    taskInstance: any;
}

interface StateToProps {
    me: any;
}

function mapStateToProps(state: CombinedState): StateToProps {
    return {
        me: state.auth.user,
    };
}

function GreyExporterComponent(props: Props & StateToProps): JSX.Element {
    const { taskInstance, me } = props;

    if (!me.isAdmin || taskInstance.timesAnnotated > 1) return false;
    return (
        <div className='task-section-container'>
            <Row className='task-section-header' type='flex' justify='start' align='middle'>
                <Col>
                    <Text className='cvat-text-color  task-section-header-text'>Export to grey</Text>
                </Col>
            </Row>
            <Row type='flex' justify='center' align='middle'>
                <Col>
                    <ExportButton taskInstance={taskInstance} />
                </Col>
            </Row>
        </div>
    );
}

export function ExportButton({taskInstance}) {
    const [loading, setLoading] = useState(false);
    const [exported, setExported] = useState(false);

    const exportTask = (): void => {
        setLoading(true);
        taskInstance.exportToGrey()
            .then(() => {
                setExported(true);
                notification.info({
                    message: 'Task has been exported to grey successfully',
                });
            }).catch((error) => {
            notification.error({
                message: 'Could not export task to grey',
                description: error.toString(),
            });
        }).finally(() => {
            setLoading(false);
        });
    };

    return (
        <Button
            loading={loading}
            disabled={loading || exported}
            type='primary'
            size='large'
            ghost
            onClick={exportTask}
        >
            Export to grey
        </Button>
    );
}

export default connect(mapStateToProps)(GreyExporterComponent);
