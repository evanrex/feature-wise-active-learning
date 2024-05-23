#!/bin/bash
#SBATCH -J sefsPBMC
#SBATCH --output=logs/out_%A.out
#SBATCH --error=logs/err_%A.err
#SBATCH -A COMPUTERLAB-SL2-CPU
#SBATCH --time=10:00:00
#SBATCH -p icelake-himem
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=24000

#! Optionally modify the environment seen by the application
#! (note that SLURM reproduces the environment at submission irrespective of ~/.bashrc):
. /etc/profile.d/modules.sh                # Leave this line (enables the module command)
module purge                               # Removes all modules still loaded
module load rhel8/default-amp              # REQUIRED - loads the basic environment


wandb agent evangeorgerex/fwal/7rkxj7g4