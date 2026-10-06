# Input data

The optimization scripts expect four NumPy arrays in this directory:

- `layer_grid.npy`: height-layer value for each grid cell.
- `installable_grid.npy`: binary mask identifying feasible CCTV installation cells.
- `ignore_grid.npy`: binary mask identifying cells excluded from coverage evaluation.
- `total_grid.npy`: binary mask defining the monitoring/evaluation area.

All four arrays should have the same two-dimensional grid shape.

The real construction-site datasets used in the paper are not included in this repository. As stated in the paper, the datasets are available upon reasonable request.
