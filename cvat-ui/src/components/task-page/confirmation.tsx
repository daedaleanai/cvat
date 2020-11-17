import { Modal } from 'antd';

export function buildConfirmDialog(options) {
    return (callback) => {
        return (...args) => {
            Modal.confirm({
                ...options,
                onOk() {
                    callback(...args);
                },
            });
        }
    };
};
