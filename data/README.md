# Input data

The optimization scripts expect four aligned NumPy arrays in this directory:

- `layer_grid.npy`: maximum height-layer index for each grid cell (`-1` where no layer point is available).
- `installable_grid.npy`: binary mask identifying feasible CCTV installation cells.
- `ignore_grid.npy`: binary mask identifying cells excluded from coverage evaluation.
- `total_grid.npy`: binary mask defining the monitoring/evaluation area.

All four arrays must have the same two-dimensional shape and coordinate origin.

## Generate the grids from PCD files

The repository includes a preprocessing utility that converts aligned site PCD inputs into these arrays:

```bash
python preprocessing/pcd_to_grids.py \
  --total "raw/total_map.pcd" \
  --layer "raw/map.pcd" \
  --installable "raw/installable_map.pcd" \
  --ignore "raw/ignore_map.pcd"
```

When `--output` is omitted, the generated arrays are written directly to this `data/` directory. See [`../preprocessing/README.md`](../preprocessing/README.md) for details, including relative-path behavior and preprocessing assumptions.

The real construction-site datasets used in the paper are not included in this repository. As stated in the paper, the datasets are available upon reasonable request.
