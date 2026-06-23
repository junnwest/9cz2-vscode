# Beagle3 Command Cheatsheet

Reference for submitting and managing jobs on Beagle3 (UChicago RCC).
Replace `<username>` with her Beagle3 username throughout.

---

## Cluster Exploration

| Command | Description |
|---------|-------------|
| `sinfo` | List all partitions and their node states (idle, alloc, mix, down) |
| `sinfo -N` | Per-node view — shows each node, its partition, CPUs, and state |
| `sinfo -N -o "%N %P %C %G %m"` | Per-node: name, partition, CPUs (alloc/idle/other/total), GPUs, memory |
| `sinfo -p <partition>` | Details for one specific partition (e.g., `sinfo -p gpu`) |
| `scontrol show partition <name>` | Full specs for a partition: max nodes, time limits, allowed accounts |
| `scontrol show node <nodename>` | Full specs for a single node: CPUs, GPUs, memory, current load |

---

## Queue Inspection

| Command | Description |
|---------|-------------|
| `squeue -p <partition>` | All jobs currently queued or running in a partition |
| `squeue -w <nodename>` | All jobs running on a specific node (e.g., `squeue -w beagle3-0001`) |
| `squeue --format='%.10i %.12j %.8u %.8T %.10M %.6D %R'` | Formatted queue with reason column — useful for diagnosing why jobs wait |
| `squeue -u <username>` | Your own jobs only |
| `squeue -u <username> --format='%.10i %.12j %.6D %.8T %.10M %.10l %Z'` | Same format as Midway3 status check |

---

## Module Management

| Command | Description |
|---------|-------------|
| `module avail` | List all available modules on Beagle3 |
| `module avail namd` | Search for NAMD modules specifically |
| `module avail alphafold` | Search for AlphaFold modules specifically |
| `module load <module>` | Load a module (e.g., `module load namd/2.14`) |
| `module list` | Show currently loaded modules |
| `module unload <module>` | Unload a module |

---

## Storage & Quota

| Command | Description |
|---------|-------------|
| `df -h /scratch/beagle3/<username>/` | How much space is used/free on your scratch |
| `du -sh <directory>` | Size of a specific directory |
| `du -sh *` | Sizes of all items in the current directory |
| `rcchelp quota` | RCC tool — your storage quota across all allocations (home, scratch, project) |
| `ls -lh` | List files with human-readable sizes |

---

## File Transfer

| Command | Description |
|---------|-------------|
| `rsync -av <src> <dst>` | Copy files/directories, preserving structure |
| `rsync -av --progress <src> <dst>` | Same with a per-file progress bar |
| `rsync -av --dry-run <src> <dst>` | Preview what would be copied without actually copying |
| `rsync -av junseo@midway3.rcc.uchicago.edu:/project2/haddadian/junseo/beagle3-jobs/ /scratch/beagle3/<username>/9cz2-jobs/` | Pull staged files from Midway3 shared space to Beagle3 scratch |
| `scp -r <src> <username>@beagle3.rcc.uchicago.edu:<dst>` | Simple copy (use rsync instead for large transfers) |

---

## Job Submission & Management

| Command | Description |
|---------|-------------|
| `sbatch <script.sbatch>` | Submit a job script |
| `scancel <jobid>` | Cancel a job by ID |
| `scancel -u <username>` | Cancel ALL your jobs (use carefully) |
| `scontrol show job <jobid>` | Full info about a job: status, node list, time left, reason if pending |
| `scontrol hold <jobid>` | Hold a job in queue without cancelling |
| `scontrol release <jobid>` | Release a held job |

---

## Job Monitoring & Output

| Command | Description |
|---------|-------------|
| `tail -f <output.out>` | Follow live output from a running job (Ctrl+C to stop) |
| `tail -n 50 <output.out>` | See last 50 lines of job output |
| `cat <error.err>` | Read the error log |
| `sacct -j <jobid>` | Job accounting: start/end time, CPU usage, exit code |
| `seff <jobid>` | Efficiency report after job completes: % CPU used, % memory used |

---

## Useful One-liners for This Meeting

| Command | Description |
|---------|-------------|
| `sinfo -N -o "%N %P %C %G %m" \| sort` | Quick overview of every node: name, partition, CPU allocation, GPUs, memory |
| `squeue -p <partition> \| wc -l` | How many jobs are in a partition's queue right now |
| `squeue --start -u <username>` | Estimated start time for your pending jobs |
| `ls -lht \| head -10` | Most recently modified files in current directory |
| `pwd` | Print current directory (sanity check before submitting) |
