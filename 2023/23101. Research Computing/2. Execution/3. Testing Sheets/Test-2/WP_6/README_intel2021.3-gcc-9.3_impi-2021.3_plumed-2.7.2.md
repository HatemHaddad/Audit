# plumed 2.7.2 with elpa fftw and scalapack compilation notes
## Introduction
Compiled on login-2 on 22th September 2021 by Sergio Martinez

## Prepare modules
    module purge
    module load intel/2021.3-gcc-9.3
    module load impi/2021.3
    module load mkl/2021.3.0
    module load zlib/1.2.11
    module load libtool/2.4.6


## Prepare directories
    ROOT_DIR=/apps/ku
    COMPILER_DEP=intel-2021_3-gcc-9_3
    MPI_DEP=impi-2021_3
    APP_NAME=plumed
    APP_VERSION=2.7.2
    APPS=${ROOT_DIR}/${COMPILER_DEP}/${MPI_DEP}/${APP_NAME}/${APP_VERSION}
    BUILD=${ROOT_DIR}/build/${APP_NAME}

    mkdir -p ${APPS}
    mkdir -p ${BUILD}

    cd ${BUILD}

    wget --no-check-certificate https://github.com/plumed/plumed2/archive/v2.7.2.tar.gz
    tar xvf v2.7.2.tar.gz
    cd plumed2-2.7.2

    wget --no-check-certificate https://github.com/hfp/xconfigure/raw/master/configure-get.sh
    chmod +x configure-get.sh
    ./configure-get.sh plumed

## Edit configure-plumed-skx.sh
    DEST=/apps/ku/intel-2021_3-gcc-9_3/impi-2021_3/plumed/2.7.2

## Configure, build and install
    make distclean
    ./configure-plumed-skx.sh
    make -j52
    make install



## Modulefile
### Location
    /apps/ku/modulefiles/MPI/intel/2021.3-gcc-9.3/impi/2021.3/plumed/2.7.2.lua
### Content
    local pkgName   = myModuleName()
    local pkgVersion = myModuleVersion()
    local pkgNameVer = myModuleFullName()
    local hierA     = hierarchyA(pkgNameVer,2)
    local mpiD      = hierA[1]:gsub("/","-"):gsub("%.","_")
    local compilerD = hierA[2]:gsub("/","-"):gsub("%.","_")
    local base      = pathJoin("/apps/ku", compilerD, mpiD, pkgNameVer)
    whatis("Name: " ..pkgName)
    whatis("Version: " .. pkgVersion)
    whatis("Description: PLUMED is an open-source, community-developed library that provides a wide range of different methods, which include: Enhanced-sampling algorithms, Free-energy methods and Tools to analyze the vast amounts of data produced by molecular dynamics simulations.")
    whatis("URL: https://www.plumed.org/")

    depends_on("mkl/2021.3.0")

    prepend_path("PATH",            pathJoin(base,"bin"))
    prepend_path("CPATH",           pathJoin(base,"include"))
    prepend_path("LD_LIBRARY_PATH", pathJoin(base,"lib"))
    prepend_path("LIBRARY_PATH",    pathJoin(base,"lib"))

    setenv("PLUMED_DIR",  base)
