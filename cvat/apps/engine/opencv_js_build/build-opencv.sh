#!/bin/bash
set -e
set -x

git clone https://github.com/opencv/opencv.git opencv
cd opencv
git checkout c722625f280258f5c865002899bf0dc2ebff1b2b
git apply ../opencv.patch

git clone https://github.com/opencv/opencv_contrib.git contrib
cd contrib
git checkout 49dde623003d6cc6cd128db2eacb9c71d3e4e3e9
git apply ../../opencv-contrib.patch
cd ..

docker run --rm --workdir /code -v "$PWD":/code "trzeci/emscripten:latest" python ./platforms/js/build_js.py build
cp build/bin/opencv.js ../../static/engine/js/3rdparty/
