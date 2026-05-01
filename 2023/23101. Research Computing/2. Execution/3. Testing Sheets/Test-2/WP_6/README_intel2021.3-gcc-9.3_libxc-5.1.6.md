# libxc 5.1.6 compilation notes
## Introduction
Compiled on cn-09-31 on 23th May 2021 by Sergio Martinez

## Prepare modules
    module purge
    module load intel/2021.3-gcc-9.3
    module load libtool/2.4.6

## Prepare directories
    ROOT_DIR=/apps/ku
    COMPILER_DEP=intel-2021_3-gcc-9_3
    APP_NAME=libxc
    APP_VERSION=5.1.6
    APPS=${ROOT_DIR}/${COMPILER_DEP}/${APP_NAME}/${APP_VERSION}
    BUILD=${ROOT_DIR}/build/${APP_NAME}

    mkdir -p ${APPS}
    mkdir -p ${BUILD}

    cd ${BUILD}
    wget --content-disposition https://www.tddft.org/programs/libxc/down.php?file=5.1.6/libxc-5.1.6.tar.gz
    tar xvf libxc-5.1.6.tar.gz
    cd libxc-5.1.6

    wget --no-check-certificate https://github.com/hfp/xconfigure/raw/master/configure-get.sh
    chmod +x configure-get.sh
    ./configure-get.sh libxc

## Edit configure-libxc-skx.sh
    DEST=/apps/ku/intel-2021_3-gcc-9_3/impi-2021_3/libxc/5.1.6
## Configure, build and install
    make distclean
    ./configure-libxc-skx.sh
    make -j52
    make install

## Modulefile
### Location
    /apps/ku/modulefiles/Compiler/intel/2021.3-gcc-9.3/libxc/5.1.6.lua
### Content
    local pkgName     = myModuleName()
    local fullVersion = myModuleVersion()
    local hierA       = hierarchyA(myModuleFullName(),1)
    local compilerD   = hierA[1]:gsub("/","-"):gsub("%.","_")
    local base        = pathJoin("/apps/ku",compilerD,pkgName,fullVersion)

    whatis("Name: "..pkgName)
    whatis("Version "..fullVersion)
    whatis("Description: Libxc is a library of exchange-correlation and kinetic energy functionals for density-functional theory. The original aim was to provide a portable, well tested and reliable set of these functionals to be used by all the codes of the European Theoretical Spectroscopy Facility (ETSF), but the library has since grown to be used in several other types of codes as well.")
    whatis("URL: https://www.tddft.org/programs/libxc/")

    prepend_path("PATH",           pathJoin(base,"bin"))
    prepend_path("CPATH",           pathJoin(base,"include"))
    prepend_path("LD_LIBRARY_PATH", pathJoin(base,"lib"))
    prepend_path("LIBRARY_PATH",    pathJoin(base,"lib"))
