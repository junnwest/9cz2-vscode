# Staged Martini equilibration — prepared Aug 3, 2026, NOT yet applied

Replaces our single 1 ns equilibration with CHARMM-GUI's 5-stage ladder, and adds the
lipid headgroup restraints our topologies never had.

**Status: staged, deliberately unapplied.** All six Martini variants (v1–v6) currently share
the same 1 ns equilibration, which makes it a controlled variable across that comparison —
changing it mid-sweep would break comparability. Apply only after the v4/v5/v6 sweep reads out.

## Where this came from

Comparison of two CHARMM-GUI builds, both in `~/Downloads/`:

| build | system | role |
|---|---|---|
| `charmm-gui-8542787498` | membrane-only | the reference we'd already compared against (Aug 1) |
| `charmm-gui-8579367020` | **1AFO** glycophorin A TM dimer | protein-in-membrane |

Diffing them answers the question that prompted this: **does CHARMM-GUI's protocol change when
a protein is present?** It does, in exactly one way — an added `-DPOSRES -DPOSRES_FC=N` ramp.
The timestep ladder and step counts are byte-identical between the two builds. So this is not a
protein-specific protocol; it's the standard ladder with a protein restraint layered on.

(1AFO was chosen over the originally-attempted 1A3N hemoglobin because hemoglobin is soluble —
no TM region, so `step2_orient` never produces a membrane-embedded system.)

## What changes

| | current `eq.mdp` | this ladder |
|---|---|---|
| stages / total | 1 / 1 ns | 5 / 4.75 ns |
| dt | 10 fs immediately | 2 → 5 → 10 → 15 → 20 fs |
| protein POSRES | 1000 → 0 (one step) | 1000 → 500 → 250 → 100 → 50 → 0 |
| lipid headgroup z | **none** | 200 → 100 → 50 → 20 → 10 → 0 |

Two settings are also corrected in passing, both inherited bugs rather than ladder changes:

- **`compressibility` 4.5e-5 → 3e-4.** 4.5e-5 is *all-atom water*; Martini water is ~7× more
  compressible. Our own `md.mdp` already used 3e-4 — `eq.mdp` was the outlier. This is the
  known-unfixed item from the Aug 1 comparison.
- `tau-p` 4.0 → 5.0 and `refcoord-scaling` com → all, matching CHARMM-GUI.

Everything else (reaction-field, `epsilon_r 15`, 1.1 nm cutoffs, `tc-grps`, v-rescale, c-rescale)
is inherited verbatim from the KALP-validated `eq.mdp`. The `em.mdp` PME/`epsilon_r` bug is **not**
addressed here — separate issue, still open.

## Applying it

### 1. Patch the lipid topologies

Our lipid `.itp`s come from `M3-Lipid-Parameters`, which carries no `[position_restraints]`
block — so `-DBILAYER_LIPIDHEAD_FC` is currently a **silent no-op**. Without this step, stages
6.2–6.6 run with protein restraints only and the lipid half of the ladder does nothing.

```bash
python3 add_lipid_headgroup_posres.py <path>/martini_ff --dry-run   # inspect first
python3 add_lipid_headgroup_posres.py <path>/martini_ff
```

Patches DPPE, POPG, DOPG (phosphate = bead 2) and TOCL (**both** phosphates, beads 2 and 13 —
cardiolipin spans the leaflet as one molecule; restraining only PO41 would tilt it). Bead indices
were read off our actual `[atoms]` blocks, not assumed from CHARMM-GUI's ordering, and the script
hard-fails if an index exceeds the molecule's atom count. Idempotent; writes `.bak` once.

Restrains **z only** (`fcx = fcy = 0`) — lateral diffusion and lipid mixing are untouched.

### 2. Run the ladder

```bash
prev=em                       # or whatever the minimized structure is
for s in step6.2 step6.3 step6.4 step6.5 step6.6; do
  gmx grompp -f ${s}_equilibration.mdp -c ${prev}.gro -r ${prev}.gro \
             -p system.top -n index.ndx -o ${s}.tpr -maxwarn 1
  gmx mdrun -deffnm ${s} -ntomp 32 -nb gpu
  prev=$s
done
```

`-r` is required — position restraints need reference coordinates. Each stage restarts from the
previous stage's `.gro`; only 6.2 generates velocities.

> **Go variants (v3/v4/v5) get no protein restraint from this.** Their topologies contain zero
> `[position_restraints]` — `martinize2 -go` was run without `-p backbone`, so `-DPOSRES` is a
> no-op there (verified: no posres in `molecule.itp`). The lipid half of the ladder still works.
> To restrain protein in a Go variant, the position-restraint block has to be generated separately.
> v1/v2 (elastic) are fine — their per-chain `.itp`s have posres on backbone beads with
> `POSRES_FC` defaulting to 1000.

## Why this is worth doing for this system

The lipid restraints are the more consequential half. This membrane needed the hand-tuned
`insane -fudge 0.9` sweep to close a 147 nm² packing void, so it starts further from equilibrium
than a routine build — and we currently go from `insane` output to 10 fs dynamics in one move.

**This is not an explanation for the dome contraction.** The all-atom systems contract too
(−3.40 Å ring width over 32 ns), so the closing is real physics. What a gentler equilibration
could plausibly change is how much early strain gets injected and how fast the contraction
happens — not whether it occurs.

## Files

- `step6.{2,3,4,5,6}_equilibration.mdp` — the ladder
- `add_lipid_headgroup_posres.py` — lipid topology patcher (`--dry-run` supported)
