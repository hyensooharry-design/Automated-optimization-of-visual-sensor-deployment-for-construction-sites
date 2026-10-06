# PCD preprocessing

`pcd_to_grids.py` converts construction-site PCD files into the four aligned NumPy grids consumed by the CCTV optimization models.

The default discretization matches the study configuration:

- horizontal grid size: **5 m**
- vertical layer height: **2 m**
- vertical layers: **25** (`0`–`24`)

All four outputs use the same XY origin and array shape derived from the `--total` point cloud.

## Installation

From the repository root:

```bash
python -m pip install -r preprocessing/requirements.txt
```

`pypcd4` is the primary PCD reader. The script can also use Open3D as a fallback if Open3D is already installed.

## Usage

From the repository root:

```bash
python preprocessing/pcd_to_grids.py \
  --total "raw/total_map.pcd" \
  --layer "raw/map.pcd" \
  --installable "raw/installable_map.pcd" \
  --ignore "raw/ignore_map.pcd"
```

If the total-area PCD is also the height source, omit `--layer`.

The default output directory is the repository-level `data/` directory, so `--output` is not required for the standard workflow.

## Path behavior

- Explicit relative input paths such as `raw/total_map.pcd` are resolved relative to the directory from which the command is executed.
- If `--output` is omitted, outputs are always written to the repository-level `data/` directory, regardless of the current working directory.
- If an explicit relative `--output` path is supplied, it is resolved relative to the current working directory.
- The optimization entry points (`precision_oriented/main.py` and `runtime_oriented/main.py`) locate the repository `data/` directory from their own file paths, so they can also be launched from a different working directory.

Absolute paths are supported as well.

## Outputs

The script writes:

- `total_grid.npy`: cells represented by the full monitoring-area PCD
- `layer_grid.npy`: maximum height-layer index observed in each cell
- `installable_grid.npy`: feasible CCTV-installation cells
- `ignore_grid.npy`: cells excluded from coverage evaluation
- `grid_metadata.json`: grid resolution, origin, shape, vertical reference, and source-file paths

Cells without height points remain `-1` in `layer_grid.npy`. The script prints a warning if an installable cell has no corresponding height-layer point.

## Important assumptions

The optimization code is configured around the paper's 5 m horizontal grid. Camera range is represented internally in grid cells, so changing `--grid-size` also requires corresponding changes to the optimization settings.

Likewise, the visibility logic uses height-layer differences. Changing `--layer-height` changes the physical meaning of the occlusion threshold and should be accompanied by a corresponding model adjustment.

The `--z-origin` option can be used to specify a fixed vertical reference. If it is omitted, the minimum Z value of the layer PCD is used.

## Full pipeline

```text
PCD files
   ↓
preprocessing/pcd_to_grids.py
   ↓
data/*.npy
   ↓
precision_oriented/main.py
or
runtime_oriented/main.py
   ↓
optimized CCTV deployment
```
