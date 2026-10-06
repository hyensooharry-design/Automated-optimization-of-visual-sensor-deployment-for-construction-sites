from algorithm.greedy import greedy_placement
from algorithm.sa import simulated_annealing
from coverage.evaluator import compute_coverage

def optimize_camera_placement(candidate_positions, grid_cells, cell_heights, layer_grid, ignore_grid,
                              camera_factory, coverage_threshold=0.9, max_iter=50, total_grid=None,
                              sa_angle_step=10, frame_dir=None, seed=42):
    print("⚙️ Greedy 단계 시작...")

    initial_cameras, initial_coverage = greedy_placement(
        candidate_positions, grid_cells, cell_heights, layer_grid, ignore_grid,
        camera_factory, coverage_threshold, total_grid=total_grid, frame_dir=frame_dir
    )

    print(f"✅ Greedy 완료 — 카메라 수: {len(initial_cameras)}, 커버리지: {len(initial_coverage)} / {len(grid_cells)} ({len(initial_coverage)/len(grid_cells):.2%})")

    print("🔥 Simulated Annealing 단계 시작...")

    final_cameras, final_coverage, log = simulated_annealing(
        initial_cameras,
        candidate_positions,
        grid_cells,
        cell_heights,
        layer_grid,
        ignore_grid,
        camera_factory,
        max_iter=max_iter,
        total_grid=total_grid,
        angle_step=sa_angle_step,
        frame_dir=frame_dir,
        seed=seed
    )

    print(f"✅ Simulated Annealing 완료 — 최종 카메라 수: {len(final_cameras)}, 커버리지: {len(final_coverage)} / {len(grid_cells)} ({len(final_coverage)/len(grid_cells):.2%})")

    combined_log = {
        "initial_camera_count": len(initial_cameras),
        "final_camera_count": len(final_cameras),
        "initial_coverage": len(initial_coverage),
        "final_coverage": len(final_coverage),
        "coverage_ratio": len(final_coverage) / len(grid_cells),
        "annealing_log": log
    }

    return final_cameras, final_coverage, combined_log
