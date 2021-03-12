import React from 'react';

import {
    Button,
    Modal,
    Slider,
    Select,
    Input,
    Checkbox,
    InputNumber,
    Form,
    Row,
    Col,
    notification,
} from 'antd';

const formItemLayout = {
    labelCol: {
        xs: {span: 24},
        sm: {span: 6},
    },
    wrapperCol: {
        xs: {span: 24},
        sm: {span: 18},
    },
};

function identityFieldCondition(frame, attrId, value) {
    if (value == null) {
        return (s) => true;
    }
    return (s) => {
        const attrs = s.interpolate(frame).attributes;
        return attrs[attrId].value == value;
    }
}

function bulkUpdateAttribute(
    start, stop, labelId, attributeName, attributeValue, identityAttrId, identityId, labelsInfo, shapeCollection
) {
    const affectedShapes = [];
    const dangerousFrames = [];
    for (let frame = start; frame < stop + 1; frame++) {
        const shapes = shapeCollection._computeInterpolation(frame).map(e => e.model);
        let filteredShapes = shapes.filter(s => s.label == labelId);
        filteredShapes = filteredShapes.filter(identityFieldCondition(frame, identityAttrId, identityId));
        if (filteredShapes.length > 1) {
            dangerousFrames.push(frame);
        } else {
            for (let shape of filteredShapes) {
                affectedShapes.push([frame, shape]);
            }
        }
    }

    if (dangerousFrames.length > 0) {
        return `Cannot change the attribute as it affects multiple objects on frames ${dangerousFrames.join(', ')}.`;
    }
    if (affectedShapes.length == 0) {
        return `There are no affected shapes within the selected range.`;
    }
    let attrInfo = labelsInfo.attrInfo(attributeName);
    const doUpdate = (batch) => {
        batch.forEach(([frame, shape, value]) => {
            if (typeof (value) === 'undefined') {
                delete shape._attributes.mutable[frame][attributeName];
                this.notify('attributes');
                return;
            }
            const attrValue = LabelsInfo.normalize(attrInfo.type, value);
            if (attrInfo.mutable) {
                shape._attributes.mutable[frame] = shape._attributes.mutable[frame] || {};
                shape._attributes.mutable[frame][attributeName] = attrValue;
                shape._setupKeyFrames();
            } else {
                shape._attributes.immutable[attributeName] = attrValue;
            }
            shape.notify('attributes');
        });
    };
    const forwardData = affectedShapes.map(([frame, shape]) => [frame, shape, attributeValue]);
    const backwardData = affectedShapes.map(([frame, shape]) => {
        let oldValue;
        if (attrInfo.mutable) {
            oldValue = shape._attributes.mutable[frame] ? shape._attributes.mutable[frame][attributeName] : undefined;
        } else {
            oldValue = shape._attributes.immutable[attributeName];
        }
        return [frame, shape, oldValue];
    });

    doUpdate(forwardData);
    window.cvat.addAction('Bulk Update Attribute', () => {
        doUpdate(backwardData);
    }, () => {
        doUpdate(forwardData);
    }, start);
    return null;
}

function AttributeEditor({ start: minFrame, stop: maxFrame, labelsInfo, shapeCollection }) {
    const [visible, setVisible] = React.useState(false);
    const [start, setStart] = React.useState(minFrame);
    const [stop, setStop] = React.useState(maxFrame);
    const [labelId, setLabelId] = React.useState(null);
    const [identityId, setIdentityId] = React.useState(null);
    const [identityAttrId, identityAttrName] = getIdentityAttribute(labelId, labelsInfo);
    const [attributeName, setAttributeName] = React.useState(null);
    const [attributeValue, setAttributeValue] = React.useState(null);
    React.useLayoutEffect(() => {
        if (identityAttrId == null && !(identityId == null)) {
            setIdentityId(null);
        }
    });
    const buttonStyle = {
        fontSize: "1.2em",
        position: "relative",
        top: "-2px"
    };

    const resetFields = () => {
        setStart(minFrame);
        setStop(maxFrame);
        setLabelId(null);
        setIdentityId(null);
        setAttributeName(null);
        setAttributeValue(null);
    };

    const handleSliderChange = ([a, b]) => {
        setStart(a);
        setStop(b);
    };

    const handleModalSubmit = () => {
        const error = bulkUpdateAttribute(
            start, stop, labelId,
            attributeName, attributeValue, identityAttrId, identityId,
            labelsInfo, shapeCollection
        );
        if (!error) {
            setVisible(false);
            resetFields();
        } else {
            notification.error({
                message: 'Cannot update the attribute',
                description: error,
            });
        }
    };

    const handleModalClose = () => {
        setVisible(false);
    };

    return (
        <>
            <Button type="primary" onClick={() => setVisible(true)} style={buttonStyle}>
                Edit Attribute
            </Button>
            <Modal
                title="Edit Attribute on multiple frames"
                visible={visible}
                onOk={handleModalSubmit}
                onCancel={handleModalClose}
                okButtonProps={{disabled: (labelId == null) || (attributeValue == null)}}
                width={780}
            >
                <Form {...formItemLayout}>
                    <Form.Item label="Frame range">
                        <RangeSlider value={[start, stop]} min={minFrame} max={maxFrame} onChange={handleSliderChange}/>
                    </Form.Item>
                    <Form.Item label="Label">
                        <Select
                            value={labelId}
                            style={{width: 120}}
                            onChange={setLabelId}
                            placeholder="Select a label"
                        >
                            {Object.entries(labelsInfo.labels()).map(([lid, labelName]) => (
                                <Select.Option value={lid}>{labelName}</Select.Option>
                            ))}
                        </Select>
                    </Form.Item>
                    {!!identityAttrId && <>
                        <Form.Item label={`Current ${identityAttrName}:`}>
                            <AttributeValueInput
                                attribute={identityAttrId}
                                labelsInfo={labelsInfo}
                                value={identityId}
                                onChange={setIdentityId}
                                leaveBlank
                            />
                        </Form.Item>
                    </>}
                    <AttributeInput
                        labelId={labelId}
                        labelsInfo={labelsInfo}
                        attribute={attributeName}
                        value={attributeValue}
                        onAttributeChange={setAttributeName}
                        onValueChange={setAttributeValue}
                    />
                </Form>
            </Modal>
        </>
    );
}

function getIdentityAttribute(labelId, labelsInfo) {
    if (labelId == null) {
        return [null, null];
    }
    const condition = ([, name]) => name === "Runway_ID" || name === "Track_id";
    const result = Object.entries(labelsInfo.labelAttributes(labelId)).find(condition);
    return  (result) ? result : [null, null];
}

function RangeSlider({ value, onChange, min, max }) {
    const [start, setStart] = React.useState(value[0]);
    const [stop, setStop] = React.useState(value[1]);
    React.useEffect(() => {
       if (value[0] != start) {
           setStart(value[0]);
       }
       if (value[1] != stop) {
           setStop(value[1]);
       }
    });
    const style = { marginLeft: 24, marginRight: 16 };

    const handleSliderChange = ([a, b]) => {
        setStart(a);
        setStop(b);
        onChange([a, b]);
    }
    const handleStartChange = (a) => {
        setStart(a);
        const b = value[1];
        if (a <= b) {
            onChange([a, b]);
        }
    }
    const handleStopChange = (b) => {
        setStop(b);
        const a = value[0];
        if (a <= b) {
            onChange([a, b]);
        }
    }

    return (
       <Row>
           <Col span={4}>
               <InputNumber
                   min={min}
                   max={max}
                   value={start}
                   onChange={handleStartChange}
               />
           </Col>
           <Col span={16}>
               <Slider range min={min} max={max} value={value} onChange={handleSliderChange} style={style} />
           </Col>
           <Col span={4}>
               <InputNumber
                   min={min}
                   max={max}
                   value={stop}
                   onChange={handleStopChange}
               />
           </Col>
       </Row>
    );
}

function AttributeInput({ labelId, labelsInfo, attribute, value, onAttributeChange, onValueChange }) {
    const handleAttributeChange = (v) => {
        onValueChange(null);
        onAttributeChange(v);
    }

    if (!labelId) {
        return null;
    }

    return (
        <Form.Item  label="Attribute:" style={{ marginBottom: 0 }}>
            <Form.Item style={{ display: 'inline-block', width: '140px' }}>
                <Select
                    value={attribute}
                    style={{width: 120}}
                    onChange={handleAttributeChange}
                >
                    {Object.entries(labelsInfo.labelAttributes(labelId)).map(([aid, attributeName]) => (
                        <Select.Option value={aid}>{attributeName}</Select.Option>
                    ))}
                </Select>
            </Form.Item>
            {attribute && <>
                <span style={{ display: 'inline-block', width: '64px', textAlign: 'center' }}>Value:</span>
                <Form.Item style={{ display: 'inline-block', width: '260px' }}>
                    <AttributeValueInput
                        attribute={attribute}
                        labelsInfo={labelsInfo}
                        value={value}
                        onChange={onValueChange}
                    />
                </Form.Item>
            </>}
        </Form.Item>
    );
}

function AttributeValueInput({ attribute, labelsInfo, value, onChange, leaveBlank=false }) {
    const attrInfo = labelsInfo.attrInfo(attribute);
    React.useLayoutEffect(() => {
        if (value == null && !leaveBlank) {
            const { defaultValue } = attrInfo;
            if (!(defaultValue == null)) {
                onChange(defaultValue);
            }
        }
    }, [attribute]);

    if (attrInfo.type === "text") {
        return <Input value={value} onChange={e => onChange(e.target.value)}/>;
    }
    if (attrInfo.type === "checkbox") {
        return <Checkbox checked={value} onChange={e => onChange(e.target.checked)}/>;
    }
    if (attrInfo.type === "radio" || attrInfo.type === "select") {
        return (
            <Select
                value={value}
                style={{ width: 120 }}
                onChange={onChange}
            >
                {attrInfo.values.map((v) => <Select.Option value={v}>{v}</Select.Option>)}
            </Select>
        );
    }
    if (attrInfo.type === "number") {
        let min = undefined;
        let max = undefined;
        let step = undefined;
        if (attrInfo.values.length === 3) {
            min = +attrInfo.values[0];
            max = +attrInfo.values[1];
            step = +attrInfo.values[2];
        }
        return <InputNumber min={min} max={max} step={step} value={value} onChange={onChange}/>;
    }
    return null;

}

export default AttributeEditor;
