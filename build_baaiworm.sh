rm -rf build
mkdir build
cd build

export PY_EXE=
export PY_BASE=
export BOOST_ROOT=

cmake ../neuronXcore -G"Unix Makefiles" \
    -DCMAKE_PREFIX_PATH="$PY_BASE" \
    -DPYTHON_EXECUTABLE="$PY_EXE" \
    -DPYTHON_LIBRARY="$PY_BASE/lib/libpython3.8.so" \
    -DPYTHON_INCLUDE_DIR="$PY_BASE/include/python3.8" \
    -DBoost_DIR="$BOOST_ROOT" \
    -DBOOST_ROOT="$BOOST_ROOT" \
    -DBoost_NO_SYSTEM_PATHS=ON \
    -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda-11.8 \
    -DOptiX_INCLUDE=/usr/local/NVIDIA-OptiX-SDK-7.0.0-linux64/include \
    -DCMAKE_C_COMPILER=gcc-11 -DCMAKE_CXX_COMPILER=g++-11

make -j8