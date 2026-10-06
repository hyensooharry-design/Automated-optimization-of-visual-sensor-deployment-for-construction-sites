# Input data

The optimization scripts expect four aligned NumPy arrays in this directory:

- `layer_grid.npy`: maximum height-layer index for each grid cell (`-1` where no height point is available).
- `installable_grid.npy`: binary mask identifying feasible CCTV installation cells.
- `ignore_grid.npy`: binary mask identifying cells excluded from coverage evaluation.
- `total_grid.npy`: binary mask defining the overall site grid represented by the full-site map.

All four arrays must have the same two-dimensional shape and coordinate origin.

## Generate the grids from three PCD files

Prepare these three PCD inputs:

- `map.pcd`: the full construction-site point cloud. It is used to generate both `total_grid.npy` and `layer_grid.npy`.
- `installable_map.pcd`: the CCTV-installable areas used to generate `installable_grid.npy`.
- `ignore_map.pcd`: the areas excluded from coverage evaluation, used to generate `ignore_grid.npy`.

The three PCD files should use the same coordinate system and spatial units.

Run the preprocessing utility from the repository root:

```bash
python preprocessing/pcd_to_grids.py \
  --map "raw/map.pcd" \
  --installable "raw/installable_map.pcd" \
  --ignore "raw/ignore_map.pcd"
```

When `--output` is omitted, the generated arrays are written directly to this `data/` directory. See [`../preprocessing/README.md`](../preprocessing/README.md) for detailed input preparation, relative-path behavior, and preprocessing assumptions.

The real construction-site datasets used in the paper are not included in this repository. As stated in the paper, the datasets are available upon reasonable request.
