def compute_coverage(cameras, grid_cells, cell_heights, layer_grid, ignore_grid=None):
    covered = set()
    for cam in cameras:
        visible = cam.get_coverage(grid_cells, cell_heights, layer_grid, ignore_grid)
        covered.update(visible)
    return covered