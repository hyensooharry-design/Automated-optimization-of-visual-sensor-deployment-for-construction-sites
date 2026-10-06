from algorithm.lahc import lahc
import time

def optimize_camera_placement(
    initial_cameras,
    initial_coverage,
    candidate_positions,
    grid_cells,
    cell_heights,
    layer_grid,
    ignore_grid,
    camera_factory,
    *,
    lahc_angle_step=10,
    lahc_history=100,
    total_time_limit=29,
    seed=42
):
    print(f"🔥 LAHC 단계 시작 (실행 제한 {total_time_limit:.2f}초)...")

    start_time = time.time()
    deadline = start_time + total_time_limit

    final_cameras, final_coverage, log = lahc(
        initial_cameras,
        candidate_positions,
        grid_cells,
        cell_heights,
        layer_grid,
        ignore_grid,
        camera_factory,
        angle_step=lahc_angle_step,
        deadline=deadline,
        L=lahc_history,
        seed=seed
    )

    print(f"✅ LAHC 완료 — 최종 카메라 수: {len(final_cameras)}, "
          f"커버리지: {len(final_coverage)} / {len(grid_cells)} "
          f"({len(final_coverage)/len(grid_cells):.2%})")

    combined_log = {
        "initial_camera_count": len(initial_cameras),
        "final_camera_count": len(final_cameras),
        "initial_coverage": len(initial_coverage),
        "final_coverage": len(final_coverage),
        "coverage_ratio": len(final_coverage) / len(grid_cells),
        "lahc_log": log
    }

    return final_cameras, final_coverage, combined_log
