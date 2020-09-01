import React, { useState } from 'react';
import {
    Row,
    Col,
    Button,
    Spin,
} from 'antd';
import Text from 'antd/lib/typography/Text';

interface Props {
    taskInstance: any;
    jobs: any[] | null;
}

function ValidationReportComponent(props: Props): JSX.Element {
    const [loading, setLoading] = useState(false);
    const [report, setReport] = useState(null);
    const { taskInstance, jobs } = props;

    const loadData = () : void => {
      setLoading(true);
      taskInstance.validate(jobs).then(responseData => {
          setReport(responseData.report);
          setLoading(false);
      })
    };

    if (loading) {
        return (<Spin size='large' className='cvat-spinner' />);
    }

    let actionButton = report ?
        <Button
            className='clear-validation-button'
            type='danger'
            size='large'
            ghost
            onClick={(): void => setReport(null)}
        >
            Clear
        </Button>
        :
        <Button
            className='trigger-validation-button'
            type='primary'
            size='large'
            ghost
            onClick={loadData}
            disabled={loading}
        >
            Validate
        </Button>
    ;

    let content = report ?
        <Row type='flex' justify='start' align='top'>
            <Col>
                <Text><pre>{report}</pre></Text>
            </Col>
        </Row>
        :
        <Row type='flex' justify='center' align='middle'>
            <Col>
                <Text strong>Press 'validate' to start validation</Text>
            </Col>
        </Row>
    ;

    return (
        <div className='validation-report-block'>
            <Row type='flex' justify='space-between' align='middle'>
                <Col>
                    <Text className='cvat-text-color  cvat-validation-header'> Validation </Text>
                </Col>
                <Col>{actionButton}</Col>
            </Row>
            {content}
        </div>
    );
}

export default ValidationReportComponent;
