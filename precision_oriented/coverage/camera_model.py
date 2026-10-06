import math
import numpy as np

class Camera:
    def __init__(self, position, fov, direction, range_limit,occlusion_delta=3):
        self.position = position
        self.fov = fov
        self.direction = direction
        self.range_limit = range_limit
        self.occlusion_delta = occlusion_delta  # 🔹추가

    def get_coverage(self, grid_cells, cell_heights, layer_grid, ignore_grid=None):
        visible_cells = set()
        x0, y0 = self.position

        # 📊 grid_cells → NumPy 배열로 변환
        grid_array = np.array(grid_cells)
        dx = grid_array[:, 0] - x0
        dy = grid_array[:, 1] - y0
        distance = np.hypot(dx, dy)
        angle = np.degrees(np.arctan2(dy, dx)) % 360

        # 📐 FOV 필터링
        lower = (self.direction - self.fov / 2) % 360
        upper = (self.direction + self.fov / 2) % 360
        if lower < upper:
            fov_mask = (angle >= lower) & (angle <= upper)
        else:
            fov_mask = (angle >= lower) | (angle <= upper)

        range_mask = distance <= self.range_limit
        mask = fov_mask & range_mask
        filtered_array = grid_array[mask]

        line_cache = {}

        for x1, y1 in filtered_array:
            if not (0 <= x1 < layer_grid.shape[1] and 0 <= y1 < layer_grid.shape[0]):
                continue
            if ignore_grid is not None and ignore_grid[y1][x1] == 1:
                continue

            key = (x0, y0, x1, y1)
            if key in line_cache:
                path = line_cache[key]
            else:
                path = self._bresenham_line_np(x0, y0, x1, y1)
                line_cache[key] = path

            blocked = False
            for x, y in path[:-1]:
                if (layer_grid[y, x] - layer_grid[y0, x0]) >= self.occlusion_delta:
                    blocked = True

            if not blocked:
                visible_cells.add((x1, y1))

        return visible_cells

    def _bresenham_line_np(self, x0, y0, x1, y1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = np.sign(x1 - x0)
        sy = np.sign(y1 - y0)

        x, y = x0, y0
        points = []

        if dx > dy:
            err = dx / 2.0
            while x != x1:
                points.append((x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                points.append((x, y))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy

        points.append((x1, y1))
        return np.array(points)