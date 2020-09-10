import React from 'react';
import { Menu } from 'antd';

export default function versionSubmenu(versionsAmount: number, render: () => JSX.Element): JSX.Element[] {
    if (versionsAmount === 1) return [render()];

    return [...Array(versionsAmount).keys()].map((version) => (
        <Menu.SubMenu key={version} title={`Version ${version+1}`}>
            {render()}
        </Menu.SubMenu>
    ));
}

