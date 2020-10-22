import React, { useState, useEffect } from 'react';
import { connect } from 'react-redux';
import Tree from 'antd/lib/tree/Tree';

import { loadShareDataAsync } from "actions/share-actions";

function mapStateToProps(state) {
    function convert(items, path) {
        return items.map((item) => {
            const isLeaf = item.type !== 'DIR';
            const key = `${path}${item.name}${isLeaf ? '' : '/'}`;
            return {
                key,
                isLeaf,
                title: item.name || 'root',
                children: convert(item.children, key),
            };
        });
    }

    const { root } = state.share;
    return {
        treeData: convert([root], ''),
    };
}

function mapDispatchToProps(dispatch) {
    return {
        getTreeData: (key, success, failure) => {
            dispatch(loadShareDataAsync(key, success, failure));
        },
    };
}

const ShareSelector = ({ value, onchange, treeData, getTreeData }) => {
    const [expandedKeys, setExpandedKeys] = useState([]);

    const loadData = (key) => new Promise((resolve, reject) => getTreeData(key, resolve, reject));
    useEffect(() => {
        loadData('/');
    }, []);

    function renderTreeNodes(data) {
        return data.map((item) => {
            if (item.children) {
                return (
                    <Tree.TreeNode
                        title={item.title}
                        key={item.key}
                        dataRef={item}
                        isLeaf={item.isLeaf}
                    >
                        {renderTreeNodes(item.children)}
                    </Tree.TreeNode>
                );
            }

            return <Tree.TreeNode key={item.key} {...item} dataRef={item} />;
        });
    }

    if (!treeData.length) {
        return <Text className='cvat-text-color'>No data found</Text>;
    }
    return (
        <Tree
            className='cvat-share-tree'
            checkable
            showLine
            checkStrictly={false}
            expandedKeys={expandedKeys}
            checkedKeys={value}
            loadData={(node) => loadData(node.props.dataRef.key)}
            onExpand={(newExpandedKeys) => setExpandedKeys(newExpandedKeys)}
            onCheck={(checkedKeys) => onchange(checkedKeys)}
        >
            { renderTreeNodes(treeData) }
        </Tree>
    );
}

export default connect(
    mapStateToProps,
    mapDispatchToProps,
)(ShareSelector);
