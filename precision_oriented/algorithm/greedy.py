import os
import numpy as np
import datetime
from coverage.evaluator import compute_coverage
from output.plotter import plot_coverage_map
from collections import Counter

def greedy_placement(candidate_positions, grid_cells, cell_heights, layer_grid, ignore_grid,
                     camera_factory, coverage_threshold=0.9, total_grid=None, frame_dir=None):
    placed_cameras = []
    covered_cells = set()
    remaining_positions = candidate_positions.copy()

    iteration = 0
    total_candidates = len(candidate_positions)

    if frame_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root_dir = os.path.dirname(base_dir)
        frame_dir = os.path.join(root_dir, "results", "precision_oriented", "frames")
    os.makedirs(frame_dir, exist_ok=True)

    while True:
        best_gain = 0
        best_camera = None
        best_position = None

        print(f"\n🔁 Greedy Iteration {iteration + 1} — 현재 커버리지: {len(covered_cells)} / {len(grid_cells)} ({len(covered_cells) / len(grid_cells):.2%})")

        for i, pos in enumerate(remaining_positions):
            for theta in range(0, 360, 60):
                cam = camera_factory(pos, theta)
                visible = cam.get_coverage(grid_cells, cell_heights, layer_grid, ignore_grid)
                gain = len(visible - covered_cells)

                if i % 100 == 0 and theta == 0:
                    print(f"   ▶ 후보 {i + 1}/{total_candidates} | 방향 {theta}° | 신규 커버 셀: {gain}")

                if gain > best_gain:
                    best_gain = gain
                    best_camera = cam
                    best_position = pos

        if best_camera is None:
            print("⚠️ 더 이상 유의미한 카메라 없음. 종료.")
            break

        placed_cameras.append(best_camera)
        covered_cells.update(best_camera.get_coverage(grid_cells, cell_heights, layer_grid, ignore_grid))
        remaining_positions.remove(best_position)

        coverage_ratio = len(covered_cells) / len(grid_cells)
        print(f"✅ 카메라 #{len(placed_cameras)} 배치 완료 | 누적 커버리지: {len(covered_cells)} / {len(grid_cells)} ({coverage_ratio:.2%})")

        frame_path = os.path.join(frame_dir, f"frame_{len(placed_cameras):03d}.png")

        coverage_count = Counter()
        for cam in placed_cameras:
            vis = cam.get_coverage(grid_cells, cell_heights, layer_grid, ignore_grid)
            for c in vis:
                coverage_count[c] += 1

        plot_coverage_map(grid_cells, placed_cameras, covered_cells, ignore_grid, frame_path, total_grid, coverage_count=coverage_count)

        if coverage_ratio >= coverage_threshold:
            print("🎯 목표 커버리지 도달. Greedy 종료.")
            break

        iteration += 1

    return placed_cameras, covered_cells
print("🕒 현재 시간:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
