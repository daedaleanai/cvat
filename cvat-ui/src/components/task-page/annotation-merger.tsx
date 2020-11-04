import React, { useState, useMemo } from 'react';
import { connect } from 'react-redux';
import {
    Row,
    Col,
    Button,
    Spin,
    notification,
    Tooltip,
    InputNumber,
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
    const [downloadUrl, setDownloadUrl] = useState(null);
    const [acceptanceScore, setAcceptanceScore] = useState(0.0);
    const [segments, setSegments] = useState([]);
    const { taskInstance, me } = props;

    const showComponent = me.isAdmin && taskInstance.timesAnnotated > 1;

    const handleAcceptSequences = (acceptedSegmentIds) => {
        function mapSegments(segments) {
            return segments.map(segment => {
                if (acceptedSegmentIds.indexOf(segment.id) === -1) {
                    return segment;
                }
                return {
                    ...segment,
                    rejected_frames_count: 0,
                    incomplete_frames_count: 0,
                };
            });
        }

        setSegments(mapSegments);
    };

    const loadData = () : void => {
      setLoading(true);
      taskInstance.mergeAnnotations(acceptanceScore)
      .then(responseData => {
          setDownloadUrl(responseData.download_url);
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

    let content;
    if (loading) {
        content = <Spin size='large' className='cvat-spinner'/>;
    } else if (segments.length) {
        content = (
            <MergeFeedbackComponent
                segments={segments}
                taskInstance={taskInstance}
                downloadUrl={downloadUrl}
                onAccept={handleAcceptSequences}
            />
        );
    } else {
        content = (
            <Row type='flex' justify='center' align='middle'>
                <Col>
                    <Text strong>Press 'Merge annotations' to start merging</Text>
                </Col>
            </Row>
        );
    }


    return (
        <div className='task-section-container'>
            <Row className='task-section-header' type='flex' justify='end' align='middle'>
                <Col>
                    <Text className='cvat-text-color task-section-header-text'> Triple annotation </Text>
                </Col>
                <Col>
                    <Tooltip title='Acceptance score'>
                        <InputNumber min={0} max={1} step={0.01} value={acceptanceScore} onChange={setAcceptanceScore} />
                    </Tooltip>
                </Col>
                <Col offset={1}>
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

function MergeFeedbackComponent({ segments, taskInstance, downloadUrl, onAccept }) {
    const [segmentIds, setSegmentIds] = useState([]);
    const [assignees, setAssignees] = useState([]);
    const [extraAnnotationRequested, setExtraAnnotationRequested] = useState(false);
    const [acceptSequencesRequested, setAcceptSequencesRequested] = useState(false);
    const getSequenceNameById = useMemo(() => buildNameGetter(segments), [segments]);

    const isExtraAnnotationAllowed = taskInstance.timesAnnotated === 3;

    const isRequestButtonEnabled = (
        !extraAnnotationRequested
        && assignees.length > 0
        && segmentIds.length > 0
        && isExtraAnnotationAllowed
    );

    const rowSelection = {
        selectedRowKeys: segmentIds,
        onChange: setSegmentIds,
        getCheckboxProps: record => ({
            disabled: record.incomplete_frames_count === 0 && record.rejected_frames_count === 0,
        }),
        hideDefaultSelections: true,
        selections: [
            {
                key: 'rejected',
                text: 'Select rejected sequences',
                onSelect: () => {
                    setSegmentIds(previousSelection => {
                        return segments
                            .filter(s => previousSelection.indexOf(s.id) >= 0 || s.rejected_frames_count > 0)
                            .map(s => s.id);
                    });
                },
            },
            {
                key: 'incomplete',
                text: 'Select incomplete sequences',
                onSelect: () => {
                    setSegmentIds(previousSelection => {
                        return segments
                            .filter(s => previousSelection.indexOf(s.id) >= 0 || s.incomplete_frames_count > 0)
                            .map(s => s.id);
                    });
                },
            },
        ],
    };

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

    const acceptSequences = () => {
        setAcceptSequencesRequested(true);
        taskInstance.acceptSequences(segmentIds)
            .then(() => {
                notification.info({
                    message: 'Given sequences has been accepted successfully',
                });
                onAccept(segmentIds);
                setSegmentIds([]);
            })
            .catch((error) => {
                console.log(error);
            })
            .finally(() => {
                setAcceptSequencesRequested(false);
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
                <Row type='flex' justify='end' align='middle'>
                    <Col span={12}>
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
                    <Col offset={1}>
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
                    <Col offset={1}>
                        <Form.Item>
                            <Button
                                type='primary'
                                size='large'
                                ghost
                                onClick={acceptSequences}
                                disabled={acceptSequencesRequested || segmentIds.length === 0}
                            >
                                Accept sequences
                            </Button>
                        </Form.Item>
                    </Col>
                </Row>
                <Row type='flex' justify='end' align='middle'>
                    <Col>
                        <Form.Item>
                            <Button
                                type='primary'
                                size='large'
                                ghost
                                onClick={() => download(downloadUrl)}
                            >
                                Download merged annotations
                            </Button>
                        </Form.Item>
                    </Col>
                    <Col  offset={1}>
                        <Form.Item>
                            <ExportButton taskInstance={taskInstance} />
                        </Form.Item>
                    </Col>
                </Row>
            </Form>
        </>
    );
}

function ExportButton({ taskInstance }) {
    const [loading, setLoading] = useState(false);
    const [exported, setExported] = useState(false);

    const exportTask = () : void => {
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

function buildNameGetter(segments) {
    const mapping = {};
    segments.forEach(s => {
        mapping[s.id] = s.sequence_name;
    });
    return (id) => mapping[id];
}

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
