def bresenham_line(x0, y0, x1, y1):
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
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
    return points

def grid_coverage_ratio(covered_cells, total_grid, ignore_grid):
    H, W = total_grid.shape
    valid_cells = [(x, y) for y in range(H) for x in range(W)
                   if total_grid[y, x] == 1 and ignore_grid[y, x] == 0]
    if not valid_cells:
        return 0.0
    return len(covered_cells) / len(valid_cells)
