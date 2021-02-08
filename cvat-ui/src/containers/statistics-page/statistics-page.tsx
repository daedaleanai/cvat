import React from 'react';
import moment from 'moment';

import {
    Col,
    Row,
    DatePicker,
} from 'antd';
import Text from 'antd/lib/typography/Text';

import StatisticsViewer from './statistics-viewer';


class StatisticsPageContainer extends React.Component {
    public constructor(props: Props) {
        super(props);
        this.state = {
            startDate: null,
            endDate: null,
        };
    }

    handleChange = (dates) => {
        if (dates.length == 0) {
            this.setState({
                startDate: null,
                endDate: null,
            });
        } else {
            const [startDate, endDate] = dates;
            this.setState({
                startDate,
                endDate,
            });
        }
    }

    public render() {
        const { startDate, endDate } = this.state;
        return (
            <>
                <Row type='flex' justify='center' align='top' className='cvat-task-details-wrapper'>
                    <Col md={22} lg={18} xl={16} xxl={14}>
                        <Row className='cvat-task-top-bar' type='flex' justify='end' align='middle'>
                            <Col>
                                <Text className='cvat-title'>Statistics</Text>
                            </Col>
                            <Col>
                                <DatePicker.RangePicker
                                    onChange={this.handleChange}
                                    ranges={{
                                        'Last two weeks': [moment().clone().subtract(14, 'days'), moment()],
                                    }}
                                />
                            </Col>
                        </Row>
                        {!!(startDate & endDate) &&
                            <div className='task-section-container'>
                                <StatisticsViewer startDate={startDate} endDate={endDate} />
                            </div>
                        }
                    </Col>
                </Row>
            </>
        );
    }
}

export default StatisticsPageContainer;
