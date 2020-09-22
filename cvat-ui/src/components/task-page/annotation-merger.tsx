import React, { useState, useMemo } from 'react';
import { connect } from 'react-redux';
import {
    Row,
    Col,
    Button,
    Spin,
    notification,
    Table,
    Form,
    Tag,
} from 'antd';
import Text from 'antd/lib/typography/Text';
import { CombinedState } from "reducers/interfaces";
import MultipleUserSelector from "components/multiple-user-selector";

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

function AnnotationMergerComponent(props: Props & StateToProps): JSX.Element {
    const [loading, setLoading] = useState(false);
    const [segments, setSegments] = useState([]);
    const { taskInstance, me } = props;

    const showComponent = me.isAdmin && taskInstance.timesAnnotated > 1;

    const loadData = () : void => {
      setLoading(true);
      taskInstance.mergeAnnotations()
      .then(responseData => {
          download(responseData.download_url);
          responseData.warnings.forEach(warning => {
            notification.warning({
                    message: 'Issue while merging annotations',
                    description: warning,
                });
          });
          setSegments(responseData.segments);
      }).catch((error) => {
          notification.error({
              message: 'Could not merge the annotations',
              description: error.toString(),
          });
      }).finally(() => {
          setLoading(false);
      })
    };

    if (!showComponent) return false;

    let content = loading ?
        <Spin size='large' className='cvat-spinner' />
        :
        segments.length ?
        <MergeFeedbackComponent segments={segments} taskInstance={taskInstance} />
        :
        <Row type='flex' justify='center' align='middle'>
            <Col>
                <Text strong>Press 'Merge annotations' to start merging</Text>
            </Col>
        </Row>
    ;

    return (
        <div className='annotation-merger-block'>
            <Row className='annotation-merger-header' type='flex' justify='end' align='middle'>
                <Col>
                    <Text className='cvat-text-color  annotation-merger-header-text'> Triple annotation </Text>
                </Col>
                <Col>
                    <Button
                        type='primary'
                        size='large'
                        ghost
                        onClick={loadData}
                        disabled={loading}
                    >
                        Merge annotations
                    </Button>
                </Col>
            </Row>
            {content}
        </div>
    );
}

function MergeFeedbackComponent({ segments, taskInstance }) {
    const [segmentIds, setSegmentIds] = useState(getInitialSelection(segments));
    const [assignees, setAssignees] = useState([]);
    const [extraAnnotationRequested, setExtraAnnotationRequested] = useState(false);
    const getSequenceNameById = useMemo(() => buildNameGetter(segments), [segments]);

    const isExtraAnnotationAllowed = taskInstance.timesAnnotated === 3;

    const isRequestButtonEnabled = (
        !extraAnnotationRequested
        && assignees.length > 0
        && segmentIds.length > 0
        && isExtraAnnotationAllowed
    );

    const rowSelection = isExtraAnnotationAllowed ? {
      selectedRowKeys: segmentIds,
      onChange: setSegmentIds,
    } : false;

    const requestExtraAnnotation = () => {
        setExtraAnnotationRequested(true);
        taskInstance.requestExtraAnnotation(segmentIds, assignees)
            .then(() => {
                notification.info({
                    message: 'Extra annotation has been created successfully',
                });
            })
            .catch((error) => {
                let description;
                if (error.segments) {
                    description = `${error.message}: ${error.segments.map(getSequenceNameById).join(', ')}.`;
                } else {
                    description = error.toString();
                }
                notification.error({
                    message: 'Could not create extra annotation',
                    description: description,
                });
                setExtraAnnotationRequested(false);
            });
    };

    return (
        <>
            <Table rowKey="id" rowSelection={rowSelection} dataSource={segments} pagination={false}>
                <Table.Column title="ID" dataIndex="dataset_id"/>
                <Table.Column title="Sequence name" dataIndex="sequence_name"/>
                <Table.Column title="Rejected:" dataIndex="rejected_frames_count" key="dataset_id" render={renderCount}/>
                <Table.Column
                    title="Needs more annotations:"
                    dataIndex="incomplete_frames_count"
                    key="dataset_id"
                    render={renderCount}
                />
                <Table.Column
                    title="Annotated by:"
                    dataIndex="annotators"
                    key="dataset_id"
                    render={annotators => (
                      <span>
                        {annotators.sort().map(annotator => (
                          <Tag color="blue" key={annotator}>
                            {annotator}
                          </Tag>
                        ))}
                      </span>
                    )}
                />
            </Table>
            <Form className="annotation-merger-request-extra">
                <Row type='flex' justify='start' align='middle'>
                    <Col span={15}>
                        <Form.Item>
                            {isExtraAnnotationAllowed &&
                                <MultipleUserSelector
                                    placeholder="Choose annotators"
                                    value={assignees}
                                    onChange={setAssignees}
                                />
                            }
                        </Form.Item>
                    </Col>
                    <Col span={7} offset={1}>
                        <Form.Item>
                            <Button
                                type='primary'
                                size='large'
                                ghost
                                onClick={requestExtraAnnotation}
                                disabled={!isRequestButtonEnabled}
                            >
                                Request extra annotation
                            </Button>
                        </Form.Item>
                    </Col>
                </Row>
            </Form>
        </>
    );
}

function buildNameGetter(segments) {
    const mapping = {}
    segments.forEach(s => {
        mapping[s.id] = s.sequence_name;
    })
    return (id) => mapping[id];
}

const getInitialSelection = (segments) => () => segments.filter(s => s.incomplete_frames_count > 0).map(s => s.id);

function renderCount(count) {
    const props = count > 0 ? {type: "danger"} : {};
    return <Text {...props}>{count}</Text>;
}

function download(url) {
    const downloadAnchor = (window.document.getElementById('downloadAnchor') as HTMLAnchorElement);
    downloadAnchor.href = url;
    downloadAnchor.click();
}

export default connect(mapStateToProps)(AnnotationMergerComponent);
