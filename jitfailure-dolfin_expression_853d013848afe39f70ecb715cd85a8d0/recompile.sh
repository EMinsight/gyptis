#!/bin/bash
# Execute this file to recompile locally
/home/bench/prg/miniconda/envs/gyptis/bin/x86_64-conda-linux-gnu-c++ -Wall -shared -fPIC -std=c++11 -O3 -fno-math-errno -fno-trapping-math -ffinite-math-only -I/home/bench/prg/miniconda/envs/gyptis/include -I/home/bench/prg/miniconda/envs/gyptis/include/eigen3 -I/home/bench/prg/miniconda/envs/gyptis/.cache/dijitso/include dolfin_expression_853d013848afe39f70ecb715cd85a8d0.cpp -L/home/bench/prg/miniconda/envs/gyptis/lib -L/home/bench/prg/miniconda/envs/gyptis/home/bench/prg/miniconda/envs/gyptis/lib -L/home/bench/prg/miniconda/envs/gyptis/.cache/dijitso/lib -Wl,-rpath,/home/bench/prg/miniconda/envs/gyptis/.cache/dijitso/lib -lmpi -lmpicxx -lpetsc -lslepc -lz -lhdf5 -lboost_timer -ldolfin -olibdijitso-dolfin_expression_853d013848afe39f70ecb715cd85a8d0.so