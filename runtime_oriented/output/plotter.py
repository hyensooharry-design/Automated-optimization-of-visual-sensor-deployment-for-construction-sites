import numpy as np
from output.visualizer import visualize_camera_map

def plot_coverage_map(grid, cameras, covered_cells, ignore_grid, save_path, total_grid, coverage_count=None):
    H, W = ignore_grid.shape
    obstacle_cells = {(x, y) for y in range(H) for x in range(W) if ignore_grid[y, x] == 1}

    visualize_camera_map(
        grid=total_grid,
        cameras=cameras,
        covered_cells=covered_cells,
        obstacle_cells=obstacle_cells,
        ignore_map=ignore_grid,
        grid_size=5.0,
        save_path=save_path,
        coverage_count=coverage_count
    )