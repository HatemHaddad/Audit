# libtool 2.4.6 compilation notes
## Introduction
Compiled on login-2 on 22nd Sep 2021 by Sergio Martinez

## Prepare modules
    module purge
    module load intel/2021.3-gcc-9.3

## Prepare directories
    ROOT_DIR=/apps/ku
    COMPILER_DEP=intel-2021_3-gcc-9_3
    APP_NAME=libtool
    APP_VERSION=2.4.6
    APPS=${ROOT_DIR}/${COMPILER_DEP}/${APP_NAME}/${APP_VERSION}
    BUILD=${ROOT_DIR}/build/${APP_NAME}

    mkdir -p ${APPS}
    mkdir -p ${BUILD}

    cd ${BUILD}
    wget http://mirror.rasanegar.com/gnu/libtool/libtool-2.4.6.tar.xz
    tar -xvf libtool-2.4.6.tar.xz
    cd libtool-2.4.6

## Configure, build and install
    mkdir -p build_2021.3-gcc-9.3
    cd build_2021.3-gcc-9.3
    export CC=icc
    export CFLAGS='-O3 -xHost -ip'
    ../configure --prefix=${APPS}
    make clean
    make -j 52
    make check
    make install

## Modulefile
### Location
    /apps/ku/modulefiles/Compiler/intel/2021.3-gcc-9.3/libtool/2.4.6.lua
### Content
    local pkgName     = myModuleName()
    local fullVersion = myModuleVersion()
    local hierA       = hierarchyA(myModuleFullName(),1)
    local compilerD   = hierA[1]:gsub("/","-"):gsub("%.","_")
    local base        = pathJoin("/apps/ku",compilerD,pkgName,fullVersion)

    whatis("Name: "..pkgName)
    whatis("Version "..fullVersion)
    whatis("Description: GNU Libtool is a generic library support script that hides the complexity of using shared libraries behind a consistent, portable interface.")
    whatis("URL: https://www.gnu.org/software/libtool/")

    prepend_path("PATH",           pathJoin(base,"bin"))
    prepend_path("CPATH",           pathJoin(base,"include"))
    prepend_path("LD_LIBRARY_PATH", pathJoin(base,"lib"))
    prepend_path("LIBRARY_PATH",    pathJoin(base,"lib"))
    prepend_path("MANPATH",         pathJoin(base,"share/man"))
