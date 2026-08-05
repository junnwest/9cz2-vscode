GaMD in NAMD GPU-RESIDENT mode -- working reference config
==========================================================

These two files are a verified-working GaMD run with CUDASOAintegrate on.
System: 24-chain HflK/HflC dome + membrane, ~1.74M atoms. Ran 5000 steps
cleanly at 8.57 ns/day (vs ~0.87 ns/day for the same system in offload mode).

  gamd-resident-test.inp   NAMD config
  run_test.sbatch          SLURM submit script


IMPORTANT: stock NAMD cannot do this
------------------------------------
NAMD 3.0.1 FATAL-errors at startup if you combine CUDASOAintegrate with
accelMD/accelMDG. You need Dr. Haochuan Chen's development branch
(gitlab.com/tcbgUIUC/namd, branch haochuan/gpu_accelmd_2, reports as
NAMD 3.1alpha4pre).

A built copy is available at:
  /scratch/beagle3/junseo/namd-chen-gpuresident/Linux-x86_64-g++/namd3

Invoke it BY FULL PATH, as run_test.sbatch does:

  module load cuda/11.5          # NOT module load namd/... -- see below
  NAMD3=/scratch/beagle3/junseo/namd-chen-gpuresident/Linux-x86_64-g++/namd3
  "$NAMD3" +p16 +devices 0,1 +setcpuaffinity your.conf > your.log

If you write a bare `namd3` instead, it resolves through PATH and the stock
namd/3.0.1-multicore-cuda module silently wins -- you'd think you were running
Chen's build and actually be on stock NAMD.


Settings that matter for resident-mode stability
------------------------------------------------
These are the ones that differ from a typical offload-mode config and are the
usual causes of "SequencerCUDA: Atoms moving too fast":

  fullElectFrequency  1     <- NOT 2. Multiple timestepping is a known friction
                               point with the resident integration loop.
  nonbondedFreq       1
  wrapWater           on    <- keep wrapping ON; without it molecules drift out
  wrapAll             on       of the cell and trigger patch-migration errors
  pairlistdist        16.0  <- 4 A buffer over cutoff 12. A 2 A buffer is tight.
  margin              5
  stepspercycle       20
  pairlistsPerCycle   2

Also: don't set cellBasisVector1/2/3 by hand if you also give extendedSystem --
after an NPT run the hardcoded numbers are stale and contradict the .xsc.


Caveats
-------
- This was a 5000-step smoke test, not a long production validation.
- It is a development branch, not a tagged NAMD release.
- Resident mode is system-dependent. Our dome-only systems run fine; our larger
  FtsH-containing systems crash with "atoms moving too fast" in resident mode
  even with correct settings, and could NOT be fixed by config tuning or by a
  minimization/velocity-reassignment warm-up. Those we run in offload mode
  (CUDASOAintegrate off) -- stable but roughly 4x slower.
- Colvars in resident mode is supported on this branch (it's why the build needs
  TCL 8.6.x rather than 8.5.9) but is the least-tested path. If you use colvars
  and hit trouble, try one run without it to isolate the cause.
