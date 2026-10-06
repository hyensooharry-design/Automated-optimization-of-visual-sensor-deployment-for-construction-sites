import math
from algorithm.utils import bresenham_line

def cast_rays_from_camera(camera, grid_cells, layer_grid):
    visible_cells = set()
    x0, y0 = camera.position
    range_limit = camera.range_limit
    fov = camera.fov
    direction = camera.direction

    lower = (direction - fov / 2) % 360
    upper = (direction + fov / 2) % 360

    filtered_targets = []
    for x1, y1 in grid_cells:
        dx, dy = x1 - x0, y1 - y0
        distance = math.hypot(dx, dy)
        if distance > range_limit:
            continue

        angle = math.degrees(math.atan2(dy, dx)) % 360
        in_fov = lower <= angle <= upper if lower < upper else angle >= lower or angle <= upper
        if in_fov:
            filtered_targets.append((x1, y1, distance, angle))

    line_cache = {}

    for x1, y1, _, _ in filtered_targets:
        key = (x0, y0, x1, y1)
        if key in line_cache:
            path = line_cache[key]
        else:
            path = bresenham_line(x0, y0, x1, y1)
            line_cache[key] = path

        blocked = False
        for x, y in path:
            if (x, y) == (x1, y1):
                continue
            if (layer_grid[y][x] - layer_grid[y0][x0]) >= getattr(camera, "occlusion_delta", 1):
                blocked = True
                break

        if not blocked:
            visible_cells.add((x1, y1))

    return visible_cells