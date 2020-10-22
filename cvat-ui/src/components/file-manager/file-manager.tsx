// Copyright (C) 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT

import './styles.scss';
import React from 'react';

import {
    Tabs,
    Icon,
    Input,
    Upload,
} from 'antd';

import { RcFile } from 'antd/lib/upload';
import Text from 'antd/lib/typography/Text';

import ExternalImagesSelector from './external-image-selector';
import ShareSelector from "./share-selector";

export interface Files {
    local: File[];
    share: string[];
    remote: string[];
}

interface State {
    files: Files;
    externalFiles: any[];
    active: 'local' | 'share' | 'remote';
}

interface Props {
    withRemote: boolean;
}

export default class FileManager extends React.PureComponent<Props, State> {
    public constructor(props: Props) {
        super(props);

        this.state = {
            files: {
                local: [],
                share: [],
                remote: [],
            },
            externalFiles: [],
            active: 'local',
        };
    }

    public getFiles(): Files {
        const {
            active,
            files,
            externalFiles,
        } = this.state;
        return {
            local: active === 'local' ? files.local : [],
            share: active === 'share' ? files.share : [],
            remote: active === 'remote' ? files.remote : [],
            externalFiles: active === 'records' ? externalFiles : [],
        };
    }

    public reset(): void {
        this.setState({
            externalFiles: [],
            active: 'local',
            files: {
                local: [],
                share: [],
                remote: [],
            },
        });
    }

    private renderLocalSelector(): JSX.Element {
        const { files } = this.state;

        return (
            <Tabs.TabPane key='local' tab='My computer'>
                <Upload.Dragger
                    multiple
                    listType='text'
                    fileList={files.local as any[]}
                    showUploadList={files.local.length < 5 && {
                        showRemoveIcon: false,
                    }}
                    beforeUpload={(_: RcFile, newLocalFiles: RcFile[]): boolean => {
                        this.setState({
                            files: {
                                ...files,
                                local: newLocalFiles,
                            },
                        });
                        return false;
                    }}
                >
                    <p className='ant-upload-drag-icon'>
                        <Icon type='inbox' />
                    </p>
                    <p className='ant-upload-text'>Click or drag files to this area</p>
                    <p className='ant-upload-hint'>
                        Support for a bulk images or a single video
                    </p>
                </Upload.Dragger>
                { files.local.length >= 5
                    && (
                        <>
                            <br />
                            <Text className='cvat-text-color'>
                                {`${files.local.length} files selected`}
                            </Text>
                        </>
                    )}
            </Tabs.TabPane>
        );
    }

    private renderShareSelector(): JSX.Element {
        const { files } = this.state;
        return (
            <Tabs.TabPane key='share' tab='Connected file share'>
                <ShareSelector
                    value={files.share}
                    onchange={(value) => {
                        this.setState((state) => ({ files : { ...state.files, share: value } }));
                    }}
                />
            </Tabs.TabPane>
        );
    }

    private renderRemoteSelector(): JSX.Element {
        const { files } = this.state;

        return (
            <Tabs.TabPane key='remote' tab='Remote sources'>
                <Input.TextArea
                    placeholder='Enter one URL per line'
                    rows={6}
                    value={[...files.remote].join('\n')}
                    onChange={(event: React.ChangeEvent<HTMLTextAreaElement>): void => {
                        this.setState({
                            files: {
                                ...files,
                                remote: event.target.value.split('\n'),
                            },
                        });
                    }}
                />
            </Tabs.TabPane>
        );
    }

    private renderRecordsSelector(): JSX.Element {
        const { externalFiles } = this.state;

        return (
            <Tabs.TabPane key='records' tab='Records service'>
                <ExternalImagesSelector
                    value={externalFiles}
                    onChange={value => this.setState({ externalFiles: value })}
                />
            </Tabs.TabPane>
        );
    }

    public render(): JSX.Element {
        const { withRemote } = this.props;
        const { active } = this.state;

        return (
            <>
                <Tabs
                    type='card'
                    activeKey={active}
                    tabBarGutter={5}
                    onChange={
                        (activeKey: string): void => this.setState({
                            active: activeKey as any,
                        })
                    }
                >
                    { this.renderLocalSelector() }
                    { this.renderShareSelector() }
                    { withRemote && this.renderRemoteSelector() }
                    { this.renderRecordsSelector() }
                </Tabs>
            </>
        );
    }
}
