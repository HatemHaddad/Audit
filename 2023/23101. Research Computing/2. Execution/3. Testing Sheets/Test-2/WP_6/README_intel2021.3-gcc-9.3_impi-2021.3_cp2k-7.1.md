# cp2k 7.1 with compilation notes
## Introduction
Compiled on cn-09-31 on 23th September 2021 by Sergio Martinez

## Prepare modules
    module purge
    module load intel/2021.3-gcc-9.3
    module load impi/2021.3
    module load mkl/2021.3.0
    module load libint/2.6.0
    module load libxsmm/1.16.2
    module load elpa/2021.05.002-omp
    module load plumed/2.7.2
    module load python/3.7.10
    module load zlib/1.2.11

## Prepare directories
    ROOT_DIR=/apps/ku
    COMPILER_DEP=intel-2021_3-gcc-9_3
    MPI_DEP=impi-2021_3
    APP_NAME=cp2k
    APP_VERSION=7.1
    APPS=${ROOT_DIR}/${COMPILER_DEP}/${MPI_DEP}/${APP_NAME}/${APP_VERSION}
    BUILD=${ROOT_DIR}/build/${APP_NAME}

    mkdir -p ${APPS}
    mkdir -p ${BUILD}

    cd ${BUILD}

    wget https://github.com/cp2k/cp2k/releases/download/v7.1.0/cp2k-7.1.tar.bz2
    tar xvf cp2k-7.1.tar.bz2
    cd cp2k-7.1

    wget --no-check-certificate https://github.com/hfp/xconfigure/raw/master/configure-get.sh
    chmod +x configure-get.sh
    ./configure-get.sh cp2k

## Configure, build and install
    rm -rf exe lib obj
    make ARCH=Linux-x86-64-intelx VERSION=psmp AVX=3 \
    LIBXSMMROOT=/apps/ku/build/libxsmm/libxsmm-1.16.2 \
    LIBINTROOT=/apps/ku/intel-2021_3-gcc-9_3/libint/2.6.0 \
    LIBXCROOT=/apps/ku/intel-2021_3-gcc-9_3/impi-2021_3/libxc/5.1.6 \
    PLUMEDROOT=/apps/ku/intel-2021_3-gcc-9_3/impi-2021_3/plumed/2.7.2 \
    ELPAROOT=/apps/ku/intel-2021_3-gcc-9_3/impi-2021_3/elpa/2021.05.002-omp -j52



## Modulefile
### Location
    /apps/ku/modulefiles/MPI/intel/2021.3-gcc-9.3/impi/2021.3/cp2k/7.1.lua
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
    whatis("Description: CP2K is a quantum chemistry and solid state physics software package that can perform atomistic simulations of solid state, liquid, molecular, periodic, material, crystal, and biological systems.")
    whatis("URL: https://www.cp2k.org/")

    depends_on("zlib/1.2.11")


    prepend_path("PATH",            pathJoin(base,"bin"))
    prepend_path("CPATH",           pathJoin(base,"include"))
    prepend_path("LD_LIBRARY_PATH", pathJoin(base,"lib"))
    prepend_path("LIBRARY_PATH",    pathJoin(base,"lib"))

    setenv("PLUMED_DIR",  base)
