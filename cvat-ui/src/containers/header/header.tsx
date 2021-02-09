// Copyright (C) 2020 Intel Corporation
//
// SPDX-License-Identifier: MIT

import { connect } from 'react-redux';

import {
    SupportedPlugins,
    CombinedState,
} from 'reducers/interfaces';

import getCore from 'cvat-core';
import HeaderComponent from 'components/header/header';
import { logoutAsync } from 'actions/auth-actions';

const core = getCore();

interface StateToProps {
    logoutFetching: boolean;
    installedAnalytics: boolean;
    installedAutoAnnotation: boolean;
    installedTFSegmentation: boolean;
    installedTFAnnotation: boolean;
    username: string;
    isStaff: boolean;
    toolName: string;
    serverHost: string;
    serverVersion: string;
    serverDescription: string;
    coreVersion: string;
    canvasVersion: string;
    uiVersion: string;
}

interface DispatchToProps {
    onLogout: typeof logoutAsync;
}

function mapStateToProps(state: CombinedState): StateToProps {
    const {
        auth: {
            fetching: logoutFetching,
            user: {
                username,
                isStaff,
            },
        },
        plugins: {
            list,
        },
        about: {
            server,
            packageVersion,
        },
    } = state;

    return {
        logoutFetching,
        installedAnalytics: list[SupportedPlugins.ANALYTICS],
        installedAutoAnnotation: list[SupportedPlugins.AUTO_ANNOTATION],
        installedTFSegmentation: list[SupportedPlugins.TF_SEGMENTATION],
        installedTFAnnotation: list[SupportedPlugins.TF_ANNOTATION],
        username,
        isStaff,
        toolName: server.name as string,
        serverHost: core.config.backendAPI.slice(0, -7),
        serverDescription: server.description as string,
        serverVersion: server.version as string,
        coreVersion: packageVersion.core,
        canvasVersion: packageVersion.canvas,
        uiVersion: packageVersion.ui,
    };
}

const mapDispatchToProps: DispatchToProps = {
    onLogout: logoutAsync,
};

export default connect(
    mapStateToProps,
    mapDispatchToProps,
)(HeaderComponent);
