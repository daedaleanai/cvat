class FrameClipper {
    constructor() {
        this._clipToFrame = false;
    }

    clamp(value, min, max) {
        return this._clipToFrame ? value : Math.clamp(value, min, max);
    }

    get clipToFrame() {
        return this._clipToFrame;
    }

    set clipToFrame(value) {
        return this._clipToFrame = value;
    }

}

window.frameClipper = new FrameClipper();
