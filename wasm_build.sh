#!/bin/bash

set -e

rm -rf cmake_build
mkdir cmake_build

pushd cmake_build

cmake \
  -DCMAKE_TOOLCHAIN_FILE=/usr/local/code/faasm/toolchain/FaasmToolchain.cmake \
  -DCMAKE_BUILD_TYPE=Release \
  ..

make

# Run WAST generation
/usr/local/code/faasm/cmake-build-debug/WAVM/bin/wavm \
   disassemble libcfaasm.so libcfaasm.wast

popd
