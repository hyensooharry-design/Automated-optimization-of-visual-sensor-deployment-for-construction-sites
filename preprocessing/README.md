# PCD preprocessing

`pcd_to_grids.py` converts three construction-site PCD inputs into the four aligned NumPy grids consumed by the CCTV optimization models.

The default discretization matches the study configuration:

- horizontal grid size: **5 m**
- vertical layer height: **2 m**
- vertical layers: **25** (`0`–`24`)

All generated grids use the same XY origin and array shape derived from the full-site `map.pcd`.

## Preparing the input PCD files

Prepare the following **three PCD files** before running the preprocessing script:

1. **`map.pcd`** — the full construction-site point cloud.  
   This single PCD defines the overall grid extent and also provides the terrain/obstacle height information used to generate `layer_grid.npy`.

2. **`installable_map.pcd`** — a point cloud containing the areas where CCTV installation is feasible.  
   These points are converted into `installable_grid.npy`.

3. **`ignore_map.pcd`** — a point cloud containing the areas that should be excluded from coverage evaluation.  
   These points are converted into `ignore_grid.npy`.

The three PCD files should use the same coordinate system and spatial units so that they can be rasterized onto one common grid.

The preprocessing script does **not** automatically infer the installable or excluded areas from `map.pcd`. Those two area-specific PCD files must therefore be prepared separately before preprocessing.

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
  --map "raw/map.pcd" \
  --installable "raw/installable_map.pcd" \
  --ignore "raw/ignore_map.pcd"
```

The default output directory is the repository-level `data/` directory, so `--output` is not required for the standard workflow.

## Path behavior

- Explicit relative input paths such as `raw/map.pcd` are resolved relative to the directory from which the command is executed.
- If `--output` is omitted, outputs are always written to the repository-level `data/` directory, regardless of the current working directory.
- If an explicit relative `--output` path is supplied, it is resolved relative to the current working directory.
- The optimization entry points (`precision_oriented/main.py` and `runtime_oriented/main.py`) locate the repository `data/` directory from their own file paths, so they can also be launched from a different working directory.

Absolute paths are supported as well.

## Outputs

The script writes:

- `total_grid.npy`: occupied cells represented by the full-site `map.pcd`
- `layer_grid.npy`: maximum height-layer index observed in each cell of `map.pcd`
- `installable_grid.npy`: feasible CCTV-installation cells derived from `installable_map.pcd`
- `ignore_grid.npy`: cells excluded from coverage evaluation, derived from `ignore_map.pcd`
- `grid_metadata.json`: grid resolution, origin, shape, vertical reference, and source-file paths

Cells without height points remain `-1` in `layer_grid.npy`. The script prints a warning if an installable cell has no corresponding height information in `map.pcd`.

## Important assumptions

The optimization code is configured around the paper's 5 m horizontal grid. Camera range is represented internally in grid cells, so changing `--grid-size` also requires corresponding changes to the optimization settings.

Likewise, the visibility logic uses height-layer differences. Changing `--layer-height` changes the physical meaning of the occlusion threshold and should be accompanied by a corresponding model adjustment.

The `--z-origin` option can be used to specify a fixed vertical reference. If it is omitted, the minimum Z value of `map.pcd` is used.

## Full pipeline

```text
map.pcd
installable_map.pcd
ignore_map.pcd
        ↓
preprocessing/pcd_to_grids.py
        ↓
data/
├── total_grid.npy
├── layer_grid.npy
├── installable_grid.npy
└── ignore_grid.npy
        ↓
precision_oriented/main.py
or
runtime_oriented/main.py
        ↓
optimized CCTV deployment
```
