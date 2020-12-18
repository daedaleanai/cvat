import React from 'react';

import { Select } from 'antd';
import Text from 'antd/lib/typography/Text';

const TASK_TYPES = ['vls', 'spotter', 'vls-lines'];

export default class TaskTypeLabel extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            isEditing: false,
        };
    }

    public render() {
        const { value, onChange } = this.props;
        if (!this.state.isEditing) {
            return (
                <Text className='cvat-text-color' onDoubleClick={this.startEdit}>{value || '-'}</Text>
            );
        }
        const handleChange = value => {
            onChange(value);
            this.finishEdit();
        };
        return (
            <Select
                defaultOpen
                value={value}
                onChange={handleChange}
                onDropdownVisibleChange={this.finishEdit}
            >
                {!value ? <Select.Option value="" disabled>-</Select.Option> : null}
                {TASK_TYPES.map((type) => <Select.Option value={type}>{type}</Select.Option>)}
            </Select>
        );
    }

    private startEdit = () => {
        return this.setState({isEditing: true});
    };

    private finishEdit = () => {
        return this.setState({isEditing: false});
    };
}
