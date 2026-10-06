# Automated Optimization of Visual Sensor Deployment for Construction Sites

Official code repository for the paper:

**Hyeonsu Jeong, Seokhee Lee, Jiwoo Kim, Jinwon Hwang, and Seonghyeon Moon, "Automated Optimization of Visual Sensor Deployment for Construction Sites," _Automation in Construction_, 192 (2026), 107264.**

DOI: https://doi.org/10.1016/j.autcon.2026.107264

## Overview

This repository contains the implementation of the visual sensor deployment framework proposed in the paper. The workflow converts construction-site point-cloud information into a grid-based representation, generates an initial CCTV deployment using a Greedy algorithm, and improves the solution using one of two optimization models.

- **Precision-oriented Model**: Greedy initialization + Simulated Annealing (SA), designed for higher-quality deployment planning when additional computation time is available.
- **Runtime-oriented Model**: candidate reduction + Greedy initialization + Late Acceptance Hill Climbing (LAHC), designed for rapid redeployment under a strict computation-time limit.

The optimization determines CCTV positions and viewing directions while considering installation feasibility, monitoring targets, camera field of view, detection range, and terrain-aware visibility.

## Repository structure

```text
.
├── README.md
├── requirements.txt
├── preprocessing/
│   ├── pcd_to_grids.py
│   ├── README.md
│   └── requirements.txt
├── data/
│   └── README.md
├── precision_oriented/
│   ├── main.py
│   ├── algorithm/
│   ├── coverage/
│   └── output/
├── runtime_oriented/
│   ├── main.py
│   ├── algorithm/
│   ├── coverage/
│   ├── output/
│   └── tests/
└── results/
    ├── precision_oriented/
    └── runtime_oriented/
```

## Experimental settings

The main experiments reported in the paper use the following common settings:

| Parameter | Setting |
|---|---:|
| Grid resolution | 5 m |
| Vertical layer height | 2 m |
| Target coverage | 95% |
| Horizontal FOV | 60° |
| Detection range | 200 m |

The model-specific hyperparameters are defined in the corresponding implementation files.

## Installation

Python 3 is required. Install the optimization dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

To generate the optimization grids directly from PCD files, also install the preprocessing dependencies:

```bash
python -m pip install -r preprocessing/requirements.txt
```

## PCD preprocessing

The preprocessing utility generates the four aligned arrays required by both optimization models:

```bash
python preprocessing/pcd_to_grids.py \
  --total "raw/total_map.pcd" \
  --layer "raw/map.pcd" \
  --installable "raw/installable_map.pcd" \
  --ignore "raw/ignore_map.pcd"
```

If `--layer` is omitted, the `--total` PCD is also used as the height source. By default, the generated arrays are written to the repository-level `data/` directory.

Relative input paths are resolved from the current working directory. The default output location is anchored to the repository itself, so the preprocessing script can be called from another working directory without redirecting the generated grids away from the optimizer's expected `data/` folder.

See [`preprocessing/README.md`](preprocessing/README.md) for the complete preprocessing and path rules.

## Input data

Both optimization models read:

```text
data/
├── layer_grid.npy
├── installable_grid.npy
├── ignore_grid.npy
└── total_grid.npy
```

All four arrays must use the same origin and shape. The preprocessing utility also writes `grid_metadata.json` with the common grid reference information.

The real construction-site datasets used in the paper are not distributed in this repository. The paper states that the datasets and code used in the study are available upon reasonable request.

## Running the models

### Precision-oriented Model

```bash
python precision_oriented/main.py
```

This model performs Greedy initialization followed by Simulated Annealing refinement.

### Runtime-oriented Model

```bash
python runtime_oriented/main.py
```

This model performs candidate reduction and Greedy initialization followed by LAHC refinement under the runtime-oriented search configuration.

Both entry points derive the `data/` and `results/` locations from their own file paths rather than the terminal's current working directory.

## Outputs

Generated files are written to:

```text
results/precision_oriented/
results/runtime_oriented/
```

Depending on the model, outputs include:

- `results.xlsx`: optimized CCTV positions, directions, coverage information, and optimization logs.
- `coverage.png`: visualization of the final deployment and covered area.
- frame images and an optimization video for the Precision-oriented Model.

The repository also retains the selected result artifacts used for the original Precision-oriented and Runtime-oriented experiments.

## Method summary

The implementation follows the main optimization pipeline presented in the paper:

1. **PCD-to-grid preprocessing**
2. **Grid-based construction-site modeling**
3. **Candidate-space reduction**
4. **Greedy initial solution generation**
5. **Metaheuristic solution refinement**
   - Simulated Annealing for the Precision-oriented Model
   - Late Acceptance Hill Climbing for the Runtime-oriented Model
6. **Deployment visualization and result export**

## Citation

If you use this code in academic work, please cite:

```bibtex
@article{jeong2026automated,
  title   = {Automated optimization of visual sensor deployment for construction sites},
  author  = {Jeong, Hyeonsu and Lee, Seokhee and Kim, Jiwoo and Hwang, Jinwon and Moon, Seonghyeon},
  journal = {Automation in Construction},
  volume  = {192},
  pages   = {107264},
  year    = {2026},
  doi     = {10.1016/j.autcon.2026.107264}
}
```
