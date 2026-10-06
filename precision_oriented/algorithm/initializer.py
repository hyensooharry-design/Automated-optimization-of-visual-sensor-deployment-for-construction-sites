from coverage.camera_model import Camera

def generate_initial_solution_with_best_angles(candidate_positions, layer_grid, ignore_grid):
    """
    각 후보 위치에서 30° 간격으로 각도를 바꿔가며
    가장 많은 셀을 가리는 각도를 선택해 초기 해를 구성.
    (Camera 시그니처/메서드에 맞게 최소 수정만 반영)
    """
    def filter_ignored(cells):
        return {cell for cell in cells if ignore_grid[cell[1], cell[0]] == 0}

    H, W = layer_grid.shape
    all_cells = [(x, y) for y in range(H) for x in range(W)]

    solution = []
    for pos in candidate_positions:
        best_theta = None
        best_coverage = set()

        for theta in range(0, 360, 60):
            # ✅ Camera 생성자 인자명/구성 맞춤
            cam = Camera(position=pos, fov=60, direction=theta, range_limit=40)

            # ✅ get_coverage로 대체 (이전 get_covered_cells 는 존재하지 않음)
            coverage = filter_ignored(cam.get_coverage(all_cells, None, layer_grid, ignore_grid))

            if len(coverage) > len(best_coverage):
                best_theta = theta
                best_coverage = coverage

        solution.append((tuple(pos), best_theta))

    return solution
