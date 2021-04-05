import React from 'react';
import ReactDOM from 'react-dom';
import 'antd/dist/antd.less';

import AttributeEditor from "./components/attribute-editor/attribute-editor";


const editorRoot = document.getElementById('range-attribute-editor-root');
if (editorRoot) {
    document.addEventListener('annotation-page-content-loaded', (event) => {
        const {start, stop, labelsInfo, shapeCollection} = event.detail;
        ReactDOM.render(
            <AttributeEditor
                start={start}
                stop={stop}
                labelsInfo={labelsInfo}
                shapeCollection={shapeCollection}
            />,
            editorRoot
        );
    });
}
