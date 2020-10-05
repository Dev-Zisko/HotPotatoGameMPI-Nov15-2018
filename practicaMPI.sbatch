#!/bin/bash
#
#SBATCH --partition=all
#SBATCH --job-name=practicaMPI_py
#SBATCH --time=1:00
#SBATCH --output=practicaMPI_py.%j.out
#SBATCH --ntasks=10

echo "-------Inicio de Proceso en mpi Python------"
prun ./practicaMPI.py
echo "-------Fin de Proceso en mpi Python------"
