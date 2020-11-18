import React from 'react';

import Text from 'antd/lib/typography/Text';

export default class TaskTypeLabel extends React.Component {
    public render(): JSX.Element {
        return (
            <Text className='cvat-text-color'>{this.props.value}</Text>
        );
    }
}
