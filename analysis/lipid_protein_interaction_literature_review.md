# Literature Review — Protein-Lipid Interaction Analysis Methods

Scope: computational methods for analyzing an existing MD trajectory (matches what we'd run on
our own simulation data, and what Rajiv's scripts do). Excludes the separate universe of
wet-lab/biochemical protein-lipid methods (lipid-overlay assays, pull-down assays, LiMA,
cross-linking proteomics, EPR) — real and standard in their own right, but not applicable here
since we're analyzing simulation output, not doing bench experiments.

## 1. Standard methods in the literature

### 1.1 Cutoff/proximity contact counting
A lipid counts as "in contact" if an atom/bead is within a cutoff of the protein. All-atom: ~3.5–6 Å heavy-atom. Coarse-grained (MARTINI): ~4.75–8.0 Å bead-level.
- [PyLipID (JCTC 2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8830038/)
- [Corey et al., cardiolipin/*E. coli* (Sci. Adv. 2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8378812/) — 0.6 nm contact cutoff
- [ProLint (NAR 2021)](https://academic.oup.com/nar/article/49/W1/W544/6285263)
- [Characterization of Lipid-Protein Interactions (Chem. Rev. 2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6506392/)

### 1.2 Depletion-Enrichment (DE) Index
Local lipid-class composition in an annular shell ÷ bulk membrane composition. >1 = enrichment, <1 = depletion.
- [Corradi et al., lipid fingerprints (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6028153/)
- [Insights into lipid-protein interactions from computer simulations (Biophys. Rev. 2021)](https://link.springer.com/article/10.1007/s12551-021-00876-9)
- [Characterization of Lipid-Protein Interactions (Chem. Rev. 2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6506392/)

### 1.3 Radial distribution function (RDF / g(r))
Density of lipid atoms as a function of distance from a reference, identifying preferred coordination-shell distances. Well-established as a standard tool for general bilayer structure (lipid-lipid RDFs: headgroup-headgroup, PO4-PO4) — less central specifically to *protein*-lipid preference than 1.1/1.2/1.4, since RDF is naturally defined relative to a point/atom, and a protein surface needs a chosen reference atom set rather than being a natural single reference point. Used for protein-lipid preference, but as a supporting analysis rather than the primary go-to method.
- Molecular dynamics simulations reveal membrane lipid interactions of Lck (*Sci. Rep.* 2022) — RDF + contact analysis for cholesterol/POPS preference (protein-lipid use)
- Shedding light on structural properties of lipid bilayers (*RSC Advances* 2019, review) — RDF as standard general bilayer-characterization tool (lipid-lipid use)

### 1.4 Residence time / contact lifetime
Duration a specific lipid stays continuously bound, not just whether it's ever nearby. Best practice: dual-cutoff (bind/unbind) scheme + biexponential survival-function fit for k_off.
- [PyLipID (JCTC 2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8830038/) — dual cutoff, biexponential fit
- [Corey et al. (Sci. Adv. 2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8378812/) — bind 0.55 nm / unbind 1.0 nm, ≥10 ns site filter
- Bayesian nonparametric residence-time analysis (2024, [bioRxiv](https://www.biorxiv.org/content/10.1101/2024.11.07.622502v1.full))

### 1.5 Density / occupancy maps ("lipid fingerprint")
2D histogram of lipid headgroup positions relative to the protein; standard grid ~0.3 nm.
- [Corradi et al., lipid fingerprints (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6028153/) — foundational, 0.3 nm grid
- [Corey et al. (Sci. Adv. 2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8378812/)

### 1.6 Purpose-built software
- [PyLipID](https://pmc.ncbi.nlm.nih.gov/articles/PMC8830038/) — dual-cutoff contacts, residence time, Louvain binding-site detection
- LiPyphilic — general lipid-membrane toolkit (order parameters, leaflets, clustering)
- [ProLint](https://academic.oup.com/nar/article/49/W1/W544/6285263) — automated contact frequency/duration/occupancy fingerprints

### 1.7 Order parameters and curvature coupling
Deuterium order parameter S_CD, directly comparable to ²H-NMR quadrupolar splitting — the standard force-field validation metric, not just a descriptive statistic. Protein-induced curvature via `MembraneCurvature` (MDAnalysis extension, not a "Bhatia et al." tool — that name belongs to a different curvature tool, MemSurfer; correcting an earlier misattribution here), typically difference-mapped against a protein-free control.
- [Acyl chain order parameters: computation from MD and comparison with ²H NMR (*Eur. Biophys. J.*)](https://pubmed.ncbi.nlm.nih.gov/17598103/)
- [On the Calculation of Acyl Chain Order Parameters from Lipid Simulations (*JCTC* 2017)](https://pubs.acs.org/doi/10.1021/acs.jctc.7b00643)
- [MembraneCurvature (MDAnalysis, GSoC 2021)](https://github.com/MDAnalysis/membrane-curvature) — DOI: 10.5281/zenodo.5553452
- [Characterization of Lipid-Protein Interactions (Chem. Rev. 2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6506392/)

### 1.8 Free energy / binding-strength calculations
Alchemical FEP — mutate a candidate site residue to alanine (or the lipid to a dummy particle), compute ΔΔG via BAR/MBAR. Established across multiple independent groups, but expensive (~50+ μs simulation per interaction) — used as a follow-up validation on a small number of high-confidence candidate sites already found by cheaper methods (1.1/1.2/1.4), not run on every lipid by default.
- [Corey et al. (Sci. Adv. 2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8378812/) — alanine scanning, 17 λ-windows
- [Insights into Membrane Protein-Lipid Interactions from Free Energy Calculations (JCTC)](https://www.biorxiv.org/content/10.1101/671750v1.full)
- [Alchemical Free Energy Calculations on Membrane-Associated Proteins (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11017255/)
- [Standard Binding Free Energy, Phospholipase C (JCIM 2021)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9795555/)

### 1.9 Binding-site sequence/structure heuristics
Predictive structural rule checkable against sequence/structure without new simulation — a lipid-recognition motif. Most established example: **CRAC/CARC** cholesterol motifs, (L/V)-X₁₋₅-(Y)-X₁₋₅-(K/R) and its mirror, phylogenetically conserved across many unrelated membrane proteins and cross-validated experimentally (monolayer binding assays, NMR). Same concept applies to cardiolipin (*E. coli*): 2-3 basic residues (Arg/Lys) within ~0.8 nm + ≥1 polar + ≥1 aromatic residue.
- [How cholesterol interacts with membrane proteins: CRAC, CARC, tilted domains](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3584320/)
- [A mirror code for protein-cholesterol interactions](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4768152/)
- [Corey et al. (Sci. Adv. 2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8378812/) — cardiolipin motif

### 1.10 Statistical significance testing
Two-tailed t-tests / Mann-Whitney U (or DE-index error bars from replicate systems) on occupancy/enrichment differences, rather than reporting raw numbers only.
- [Corey et al. (Sci. Adv. 2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8378812/) — t-tests
- Molecular dynamics simulations of lipid-protein interactions in SLC4 proteins (*Biophys. J.* 2024) — t-test / Mann-Whitney U
- [Corradi et al., lipid fingerprints (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6028153/) — DE-index error bars across replicate systems

### 1.11 Experimental structure cross-validation
Check simulation-derived binding sites/rules against real experimental structures. Established enough to have dedicated tooling, not just an ad hoc check.
- [Corey et al. (Sci. Adv. 2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8378812/) — PDB mining, 222 CDL-containing structures
- [PyLipID (JCTC 2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8830038/) — validated top-residence-time site against cryo-EM PIP2 site (PDB 6T9N) and a cardiolipin crystal site
- [Discovery of lipid binding sites in a ligand-gated ion channel by integrating simulations and cryo-EM (eLife 2023)](https://elifesciences.org/articles/86016)
- [LipIDens — simulation-assisted interpretation of cryo-EM lipid densities (bioRxiv 2022)](https://www.biorxiv.org/content/10.1101/2022.06.30.498233v1.full) — dedicated pipeline for this validation

### 1.12 Markov State Models (kinetics beyond simple residence time)
Discretizes the trajectory into microstates (e.g. bound/unbound/intermediate conformations) and estimates transition probabilities between them, capturing multi-state binding kinetics that a single residence-time number can't (e.g. distinguishing "loosely annular," "specifically bound," and intermediate states, with rates between each). More established for general ligand/protein-protein kinetics than lipid-specific work, but does appear directly in the protein-lipid literature, mainly for GPCR-lipid/cholesterol systems.
- [GPCR Oligomerisation Modulation by Conformational State and Lipid Interactions Revealed by MD Simulations and Markov Models (bioRxiv 2020)](https://www.biorxiv.org/content/10.1101/2020.06.24.168260v1.full)
- [A critical perspective on Markov state model treatments of protein–protein association using coarse-grained simulations (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7902085/) — general caveats/limitations of MSMs for coarse-grained data, directly relevant if adopting this approach

### 1.13 Machine learning / predictive models
Emerging category (mostly 2022+): train a model (autoencoder, ensemble classifier, etc.) on MD-derived contact/interaction data to predict lipid-binding residues, protein-membrane interfaces, or proteome-wide lipid-interacting proteins, rather than measuring interactions directly from a single trajectory. Complements 1.9's hand-crafted sequence motifs with learned patterns instead. Real and growing, but newer/less standardized than 1.1-1.11 — not yet a default step in most protein-lipid MD papers.
- [Predicting protein-lipid interactions through machine learning methods employing new tokenization techniques (*Biophys. J.* 2023)](https://www.cell.com/biophysj/fulltext/S0006-3495(22)03627-X)
- [Machine learning–driven multiscale modeling reveals lipid-dependent dynamics of RAS signaling proteins (*PNAS*)](https://www.pnas.org/doi/10.1073/pnas.2113297119)
- [A machine learning model for the proteome-wide prediction of lipid-interacting proteins (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10862712/)
- [Predicting protein–membrane interfaces of peripheral membrane proteins using ensemble machine learning (*Brief. Bioinform.*)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8921665/)

## 2. General bilayer-property analysis (protein-independent)

Standard methods that characterize the membrane itself — not how it relates to a protein. Included
because some (thickness, curvature) already overlap with what Rajiv's scripts do in a
protein-relative way, and others could matter for the composition-vs-opening question even without
being "protein-lipid interaction" methods per se.

### 2.1 Area per lipid (APL)
2D Voronoi tessellation of lipid centers-of-mass projected onto the bilayer plane; each lipid's Voronoi-cell area is its instantaneous APL. Standard for detecting local packing/crowding differences (e.g., near a large embedded protein vs. bulk).
- [Membrane simulation analysis using Voronoi tessellation (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3980144/)
- [Analysis of lipid surface area in protein-membrane systems combining Voronoi Tessellation and Monte Carlo integration (*J. Comput. Chem.* 2012)](https://onlinelibrary.wiley.com/doi/abs/10.1002/jcc.21973) — explicitly protein-membrane context
- [Computing Individual Area per Head Group Reveals Lipid Bilayer Dynamics (*JPCB* 2022)](https://pubs.acs.org/doi/abs/10.1021/acs.jpcb.2c04633)

### 2.2 Bilayer thickness
Already in Rajiv's pipeline (`thickness.py`, `diff_thick.py`) — headgroup phosphate z-position mapped in 2D, typically difference-mapped against a protein-free control (same pattern as the curvature scripts). Standard, textbook method.
- Shedding light on structural properties of lipid bilayers (*RSC Advances* 2019, review) — thickness alongside APL, diffusion, order parameters as the standard general-property set

### 2.3 Lateral diffusion coefficient (MSD)
Mean-squared displacement of lipid centers-of-mass over time, fit via the Einstein relation to get a diffusion coefficient. Important caveat: MSD is non-linear ("subdiffusive," cage effect) for roughly the first 10-30 ns — fits must skip that early window or the diffusion coefficient is wrong. Could show whether lipids near the dome move more slowly/are more "caged" than bulk.
- [Subdiffusion and lateral diffusion coefficient of lipid atoms and molecules in phospholipid bilayers (*Phys. Rev. E*)](https://link.aps.org/doi/10.1103/PhysRevE.79.011907)
- [Dynamics of Lipids, Cholesterol, and Transmembrane α-Helices from Microsecond MD Simulations (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4254001/) — protein-adjacent lipid dynamics specifically

### 2.4 Membrane undulation spectrum / bending modulus (Helfrich analysis)
Fits the Fourier spectrum of thermal bilayer height fluctuations to the Helfrich continuum model to extract the bending rigidity κ. Real caveat found in the literature: needs very large systems and long trajectories to resolve the slow, long-wavelength modes accurately — likely not practical at your current system size/trajectory length.
- [Calculating the Bending Modulus for Multicomponent Lipid Membranes in Different Thermodynamic Phases (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3770052/)
- [Bending Modulus of Lipid Membranes from Density Correlation Functions (*JCTC* 2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9097289/) — newer alternative avoiding the huge-system requirement

### 2.5 Leaflet asymmetry / lipid flip-flop
Tracks whether lipid composition differs between the two leaflets, and (rarely) direct transverse flip-flop events. General caveat: flip-flop is a genuinely rare event on standard atomistic MD timescales — not something you'd expect to observe directly without specialized enhanced-sampling methods (e.g. AI-guided transition path sampling).

**Directly relevant to this project, not just generic**: Ghanbarpour et al. 2025 (EMBO J., the primary 9CZ2 structural paper) reports that the membrane *inside* the FtsH•HflK/C complex curves **opposite** to the surrounding inner membrane (confirmed in detergent and nanodisc preps, not an artifact), and *experimentally demonstrates* (NBD-lipid dithionite-quenching assay) that both FtsH alone and the full complex **enhance lipid scrambling (flip-flop)** — citing the general principle that unusual curvature correlates with easier head-group flipping. They propose local membrane **thinning** as the mechanism, and speculate the same thinning may assist substrate extraction during proteolysis (ATP-independent, so mechanistically separate from the protease motor). This directly connects flip-flop to **2.2 (thickness)** and to Rajiv's existing curvature scripts — comparing thinning/curvature specifically at the dome opening vs. elsewhere would be a direct computational test of this paper's own hypothesis, not a new speculative direction.
- [Ghanbarpour et al., asymmetric nautilus-like HflK/C assembly (*EMBO J.* 2025, PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12048511/) — curvature inversion + experimental scramblase assay
- [Simulations of Asymmetric Membranes Illustrate Cooperative Leaflet Coupling and Lipid Adaptability (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7396604/)
- [AI-guided transition path sampling of lipid flip-flop and membrane nanoporation (*Nat. Commun.*)](https://www.nature.com/articles/s41467-025-67599-3)
- [Building Asymmetric Lipid Bilayers for MD Simulations: What Methods Exist and How to Choose One? (*MDPI*)](https://www.mdpi.com/2077-0375/13/7/629)

### 2.6 Electron density profiles (X-ray/neutron scattering comparison)
Fourier transform of the simulated electron density profile, compared directly against experimental small-angle X-ray/neutron scattering data — the main way simulated bilayer structure gets externally, experimentally validated (analogous to how order parameters get validated against ²H-NMR).
- [Interpretation of small angle X-ray measurements guided by MD simulations of lipid bilayers (PubMed)](https://pubmed.ncbi.nlm.nih.gov/14623455/)
- [Determination of Electron Density Profiles and Area from Simulations of Undulating Membranes (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3149245/)

### 2.7 Packing defects / free volume
Grid-based topographic scan of the bilayer surface identifying cavities where hydrophobic (acyl chain) atoms are exposed at the surface rather than shielded by headgroups. Directly relevant to peripheral-protein insertion, and has a dedicated, actively maintained tool.
- [PackMem: A Versatile Tool to Compute and Visualize Interfacial Packing Defects in Lipid Bilayers (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6084522/) — [tool](https://packmem.ipmc.cnrs.fr/)
- [Efficient quantification of lipid packing defect sensing by amphipathic peptides (bioRxiv)](https://www.biorxiv.org/content/10.1101/2022.03.04.482978.full.pdf) — Martini vs. CHARMM36 comparison
