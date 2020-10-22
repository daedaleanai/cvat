// Copyright (C) 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT

import React from 'react';

import FileManagerComponent, { Files } from 'components/file-manager/file-manager';


interface Props {
    ref: any;
    withRemote: boolean;
}

export class FileManagerContainer extends React.PureComponent<Props> {
    private managerComponentRef: any;

    public getFiles(): Files {
        return this.managerComponentRef.getFiles();
    }

    public reset(): Files {
        return this.managerComponentRef.reset();
    }

    public render(): JSX.Element {
        const {
            withRemote,
        } = this.props;

        return (
            <FileManagerComponent
                withRemote={withRemote}
                ref={(component): void => {
                    this.managerComponentRef = component;
                }}
            />
        );
    }
}

export default FileManagerContainer;
