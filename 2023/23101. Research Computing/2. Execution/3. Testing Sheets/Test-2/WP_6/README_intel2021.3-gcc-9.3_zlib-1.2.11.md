# zlib 1.2.11 compilation notes
## Introduction
Compiled on login-2 on 16th May 2021 by Sergio Martinez

## Prepare modules
    module purge
    module load intel/2021.3-gcc-9.3

## Prepare directories
    ROOT_DIR=/apps/ku
    COMPILER_DEP=intel-2021_3-gcc-9_3
    APP_NAME=zlib
    APP_VERSION=1.2.11
    APPS=${ROOT_DIR}/${COMPILER_DEP}/${APP_NAME}/${APP_VERSION}
    BUILD=${ROOT_DIR}/build/${APP_NAME}

    mkdir -p ${APPS}
    mkdir -p ${BUILD}

    cd ${BUILD}
    wget https://zlib.net/zlib-1.2.11.tar.gz
    tar -xvf zlib-1.2.11.tar.gz
    cd zlib-1.2.11

## Configure, build and install
    mkdir -p build_2021.3-gcc-9.3
    cd build_2021.3-gcc-9.3
    export CC=icc
    CFLAGS='-O3 -xHost -ip'
    ../configure --prefix=${APPS}
    make clean
    make -j 52
    make check
    make install

## Modulefile
### Location
    /apps/ku/modulefiles/Compiler/intel/2021.3-gcc-9.3/zlib/1.2.11.lua
### Content
    local pkgName     = myModuleName()
    local fullVersion = myModuleVersion()
    local hierA       = hierarchyA(myModuleFullName(),1)
    local compilerD   = hierA[1]:gsub("/","-"):gsub("%.","_")
    local base        = pathJoin("/apps/ku",compilerD,pkgName,fullVersion)

    whatis("Name: "..pkgName)
    whatis("Version "..fullVersion)
    whatis("Description: zlib is a software library used for data compression. zlib was written by Jean-loup Gailly and Mark Adler and is an abstraction of the DEFLATE compression algorithm used in their gzip file compression program.")
    whatis("URL: https://zlib.net/")

    prepend_path("CPATH",           pathJoin(base,"include"))
    prepend_path("LD_LIBRARY_PATH", pathJoin(base,"lib"))
    prepend_path("LIBRARY_PATH",    pathJoin(base,"lib"))
    prepend_path("MANPATH",         pathJoin(base,"share/man"))
