import React, { useState } from 'react';
import { connect } from 'react-redux';
import {
    Row,
    Col,
    Button,
    Spin,
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
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');
    const [exported, setExported] = useState(false);

    const exportTask = () : void => {
      setLoading(true);
      taskInstance.exportToGrey()
      .then(() => {
          setExported(true);
      }).catch((error) => {
          if (typeof error === 'string') {
              setErrorMessage(error);
          } else {
              console.log(error);
          }
      }).finally(() => {
          setLoading(false);
      })
    };

    if (!me.isAdmin) return false;

    let content;
    if (loading) {
        content = <Spin size='large' className='cvat-spinner' />;
    } else if (errorMessage) {
        content = <Text type="danger"><pre>{errorMessage}</pre></Text>;
    } else if (exported) {
        content = "The task has been exported successfully";
    } else {
        content = (
            <Button
                type='primary'
                size='large'
                ghost
                onClick={exportTask}
            >
                Export
            </Button>
        );
    }

    return (
        <div className='task-section-container'>
            <Row className='task-section-header' type='flex' justify='start' align='middle'>
                <Col>
                    <Text className='cvat-text-color  task-section-header-text'>Export to grey</Text>
                </Col>
            </Row>
            <Row type='flex' justify='center' align='middle'>
                <Col>
                    {content}
                </Col>
            </Row>
        </div>
    );
}

export default connect(mapStateToProps)(GreyExporterComponent);
