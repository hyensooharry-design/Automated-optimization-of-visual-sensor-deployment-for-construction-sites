from coverage.camera_model import Camera

def generate_initial_solution_with_best_angles(candidate_positions, grid_cells, cell_heights, layer_grid, ignore_grid):
    def filter_ignored(cells):
        return {cell for cell in cells if ignore_grid[cell[1], cell[0]] == 0}

    solution = []
    for pos in candidate_positions:
        best_theta = None
        best_coverage = set()

        for theta in range(0, 360, 30):
            cam = Camera(position=pos, fov=60, direction=theta, range_limit=40)

            coverage = filter_ignored(
                cam.get_coverage(grid_cells, cell_heights, layer_grid, ignore_grid)
            )

            if len(coverage) > len(best_coverage):
                best_theta = theta
                best_coverage = coverage

        solution.append(Camera(position=pos, fov=60, direction=best_theta, range_limit=40))

    return solution
