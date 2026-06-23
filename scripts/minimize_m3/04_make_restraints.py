#!/usr/bin/env python3
"""
Generate restraint PDB for NAMD minimization:
  B = 0.0  for M3 residues (resid 356-419) on HflK chains (A,C,E,G,I,K,M,O,Q,S,U,X)
  B = 500.0 for everything else (dome, water, ions)
"""

IN_PDB  = "/scratch/midway3/junseo/26summer-research/minimize_m3/dome_m3_ionized.pdb"
OUT_PDB = "/scratch/midway3/junseo/26summer-research/minimize_m3/restraints.pdb"

HFLK_CHAINS = set("ACEGIKMOQSUX")
M3_START    = 356
M3_END      = 419

with open(IN_PDB) as fin, open(OUT_PDB, "w") as fout:
    for line in fin:
        if line.startswith(("ATOM", "HETATM")):
            chain = line[21]
            try:
                resid = int(line[22:26].strip())
            except ValueError:
                resid = -1

            if chain in HFLK_CHAINS and M3_START <= resid <= M3_END:
                bfac = 0.0   # free to move
            else:
                bfac = 500.0  # restrained

            line = line[:60] + f"{bfac:6.2f}" + line[66:]
        fout.write(line)

print(f"Restraint PDB written to {OUT_PDB}")
print("  B=0   -> M3 (resid 356-419) on HflK chains A,C,E,G,I,K,M,O,Q,S,U,X")
print("  B=500 -> everything else")
