"""Create aligned grid inputs for the visual-sensor optimization code.

All four generated arrays share the coordinate origin and shape derived from
``--map``. The same full-site map PCD is used both to define the spatial
extent and to generate the height-layer grid. The default settings reproduce
the grid discretization used by the study: 5 m horizontal cells and 2 m
vertical layers.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data"


def load_xyz(path: Path) -> np.ndarray:
    """Read XYZ points from a PCD file.

    pypcd4 is preferred because it supports ASCII, binary, and
    binary-compressed PCD files.  If it is unavailable, Open3D is used as a
    fallback when installed.
    """
    pypcd_error: Exception | None = None
    try:
        from pypcd4 import PointCloud
    except ImportError:
        PointCloud = None

    if PointCloud is not None:
        try:
            cloud = PointCloud.from_path(path)
        except Exception as exc:  # allow Open3D fallback for unsupported PCD variants
            pypcd_error = exc
        else:
            names = {name.lower(): name for name in cloud.pc_data.dtype.names or ()}
            missing = {axis for axis in ("x", "y", "z") if axis not in names}
            if missing:
                raise ValueError(f"Missing PCD fields: {', '.join(sorted(missing))}")
            return np.column_stack(
                [cloud.pc_data[names[axis]].astype(np.float64) for axis in ("x", "y", "z")]
            )

    try:
        import open3d as o3d
    except ImportError as exc:
        detail = f" pypcd4 error: {pypcd_error}" if pypcd_error is not None else ""
        raise RuntimeError(
            "Unable to read the PCD. Install pypcd4 (recommended), or Open3D as a fallback."
            + detail
        ) from exc

    cloud = o3d.io.read_point_cloud(str(path))
    return np.asarray(cloud.points, dtype=np.float64)


def clean_xyz(points: np.ndarray, label: str) -> np.ndarray:
    """Validate XYZ shape and remove non-finite points."""
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"{label} PCD does not contain an Nx3 XYZ array.")
    finite = np.isfinite(points).all(axis=1)
    cleaned = points[finite]
    if len(cleaned) == 0:
        raise ValueError(f"{label} PCD does not contain usable finite XYZ points.")
    if len(cleaned) != len(points):
        print(f"Warning: removed {len(points) - len(cleaned)} non-finite points from {label} PCD.")
    return cleaned


def make_reference_grid(points: np.ndarray, grid_size: float) -> tuple[float, float, int, int]:
    x_min, y_min = points[:, :2].min(axis=0)
    x_max, y_max = points[:, :2].max(axis=0)
    # +1 retains points that fall exactly on the maximum grid boundary.
    n_cols = int(np.floor((x_max - x_min) / grid_size)) + 1
    n_rows = int(np.floor((y_max - y_min) / grid_size)) + 1
    return float(x_min), float(y_min), n_rows, n_cols


def indices(
    points: np.ndarray, x_min: float, y_min: float, grid_size: float
) -> tuple[np.ndarray, np.ndarray]:
    x_idx = np.floor((points[:, 0] - x_min) / grid_size).astype(np.int64)
    y_idx = np.floor((points[:, 1] - y_min) / grid_size).astype(np.int64)
    return x_idx, y_idx


def rasterize_binary(
    points: np.ndarray,
    x_min: float,
    y_min: float,
    n_rows: int,
    n_cols: int,
    grid_size: float,
) -> np.ndarray:
    grid = np.zeros((n_rows, n_cols), dtype=np.uint8)
    x_idx, y_idx = indices(points, x_min, y_min, grid_size)
    valid = (0 <= x_idx) & (x_idx < n_cols) & (0 <= y_idx) & (y_idx < n_rows)
    grid[y_idx[valid], x_idx[valid]] = 1
    return grid


def rasterize_layers(
    points: np.ndarray,
    x_min: float,
    y_min: float,
    n_rows: int,
    n_cols: int,
    grid_size: float,
    layer_height: float,
    max_layer: int,
    z_origin: float,
) -> np.ndarray:
    grid = np.full((n_rows, n_cols), -1, dtype=np.int16)
    x_idx, y_idx = indices(points, x_min, y_min, grid_size)
    layer_idx = np.floor((points[:, 2] - z_origin) / layer_height).astype(np.int64)
    layer_idx = np.clip(layer_idx, 0, max_layer)
    valid = (0 <= x_idx) & (x_idx < n_cols) & (0 <= y_idx) & (y_idx < n_rows)
    # Keep the highest point layer in every horizontal grid cell.
    np.maximum.at(grid, (y_idx[valid], x_idx[valid]), layer_idx[valid])
    return grid


def resolve_input_path(path_text: str) -> Path:
    """Resolve an explicit CLI path relative to the current working directory."""
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def resolve_output_path(path_text: str | None) -> Path:
    """Use repo-root/data by default; explicit relative paths use the current working directory."""
    if path_text is None:
        return DEFAULT_OUTPUT_DIR.resolve()
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def read_required(path_text: str, label: str) -> tuple[Path, np.ndarray]:
    path = resolve_input_path(path_text)
    if not path.is_file():
        raise FileNotFoundError(f"{label} PCD was not found: {path}")
    points = clean_xyz(load_xyz(path), label)
    return path, points


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert PCD files into aligned grid inputs for CCTV optimization."
    )
    parser.add_argument(
        "--map",
        required=True,
        help="Full-site PCD used for both grid extent and terrain/obstacle height layers.",
    )
    parser.add_argument("--installable", required=True, help="PCD of feasible camera-installation areas.")
    parser.add_argument("--ignore", required=True, help="PCD of areas excluded from coverage evaluation.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory. Default: the repository's data/ directory.",
    )
    parser.add_argument("--grid-size", type=float, default=5.0, help="Grid-cell size in metres (default: 5.0).")
    parser.add_argument(
        "--layer-height", type=float, default=2.0, help="Vertical height per layer in metres (default: 2.0)."
    )
    parser.add_argument(
        "--max-layer",
        type=int,
        default=24,
        help="Maximum stored layer index (default: 24, i.e. 25 layers indexed 0-24).",
    )
    parser.add_argument(
        "--z-origin",
        type=float,
        default=None,
        help="Optional vertical reference elevation in metres. Default: minimum Z of the map PCD.",
    )
    args = parser.parse_args()

    if args.grid_size <= 0 or args.layer_height <= 0 or args.max_layer < 0:
        parser.error("grid-size and layer-height must be positive; max-layer must be zero or greater.")

    map_path, map_points = read_required(args.map, "Map")
    installable_path, installable_points = read_required(args.installable, "Installable-area")
    ignore_path, ignore_points = read_required(args.ignore, "Ignore-area")

    x_min, y_min, n_rows, n_cols = make_reference_grid(map_points, args.grid_size)
    z_origin = float(map_points[:, 2].min()) if args.z_origin is None else float(args.z_origin)

    total_grid = rasterize_binary(map_points, x_min, y_min, n_rows, n_cols, args.grid_size)
    installable_grid = rasterize_binary(installable_points, x_min, y_min, n_rows, n_cols, args.grid_size)
    ignore_grid = rasterize_binary(ignore_points, x_min, y_min, n_rows, n_cols, args.grid_size)
    layer_grid = rasterize_layers(
        map_points,
        x_min,
        y_min,
        n_rows,
        n_cols,
        args.grid_size,
        args.layer_height,
        args.max_layer,
        z_origin,
    )

    output_dir = resolve_output_path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / "total_grid.npy", total_grid)
    np.save(output_dir / "layer_grid.npy", layer_grid)
    np.save(output_dir / "installable_grid.npy", installable_grid)
    np.save(output_dir / "ignore_grid.npy", ignore_grid)

    metadata = {
        "grid_size_m": args.grid_size,
        "layer_height_m": args.layer_height,
        "max_layer": args.max_layer,
        "z_origin_m": z_origin,
        "origin_xy": [x_min, y_min],
        "shape_rows_cols": [n_rows, n_cols],
        "source_files": {
            "map": str(map_path),
            "installable": str(installable_path),
            "ignore": str(ignore_path),
        },
    }
    (output_dir / "grid_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Created aligned {args.grid_size:g} m grids in: {output_dir}")
    print(f"Shape: {n_rows} rows x {n_cols} columns; origin: ({x_min:.3f}, {y_min:.3f})")
    print(f"Vertical reference: z={z_origin:.3f} m; layer height: {args.layer_height:g} m")
    for name, grid in {
        "total_grid": total_grid,
        "installable_grid": installable_grid,
        "ignore_grid": ignore_grid,
    }.items():
        print(f"{name}: {int(grid.sum())} marked cells")

    missing_layer_installable = (installable_grid == 1) & (layer_grid < 0)
    if np.any(missing_layer_installable):
        print(
            "Warning: "
            f"{int(missing_layer_installable.sum())} installable cells have no layer points. "
            "Check the map PCD before optimization."
        )


if __name__ == "__main__":
    main()
