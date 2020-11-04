import React, { useState } from 'react';
import {
    Row,
    Col,
    Button,
    Select,
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
    const [version, setVersion] = useState("0");
    const { taskInstance, jobs } = props;

    const showVersionSelector = !report && !jobs && taskInstance.timesAnnotated > 1;

    const loadData = () : void => {
      setLoading(true);
      const jobSelection = { jobs, version: showVersionSelector ? version : null };
      taskInstance.validate(jobSelection).then(responseData => {
          setReport(responseData.report);
          setLoading(false);
      })
    };

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

    let content;
    if (loading) {
        content = <Spin size='large' className='cvat-spinner' />;
    } else if (report) {
        content = (
            <Row type='flex' justify='start' align='top'>
                <Col>
                    <Text><pre>{report}</pre></Text>
                </Col>
            </Row>
        );
    } else {
        content = (
            <Row type='flex' justify='center' align='middle'>
                <Col>
                    <Text strong>Press 'validate' to start validation</Text>
                </Col>
            </Row>
        );
    }

    return (
        <div className='task-section-container'>
            <Row className='task-section-header' type='flex' justify='end' align='middle'>
                <Col>
                    <Text className='cvat-text-color  cvat-validation-header'> Validation </Text>
                </Col>
                {showVersionSelector && <Col span={1} offset={1}>
                    <Select value={version} onChange={value => setVersion(value)}>
                        {[...Array(taskInstance.timesAnnotated).keys()]
                            .map((v) => <Select.Option key={v} value={String(v)}>{v+1}</Select.Option>
                        )}
                    </Select>
                </Col>}
                <Col offset={1}>{actionButton}</Col>
            </Row>
            {content}
        </div>
    );
}

export default ValidationReportComponent;
