import os
import numpy as np
import datetime
from collections import Counter
from algorithm.optimizer import optimize_camera_placement
from output.save_excel import save_results_to_excel
from output.plotter import plot_coverage_map
from coverage.camera_model import Camera
from algorithm.greedy import greedy_placement


def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(BASE_DIR)
    DATA_DIR = os.path.join(ROOT_DIR, "data")
    OUTPUT_DIR = os.path.join(ROOT_DIR, "results", "runtime_oriented")
    FRAME_DIR = os.path.join(OUTPUT_DIR, "frames")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    layer_grid_path = os.path.join(DATA_DIR, "layer_grid.npy")
    installable_grid_path = os.path.join(DATA_DIR, "installable_grid.npy")
    ignore_grid_path = os.path.join(DATA_DIR, "ignore_grid.npy")
    total_grid_path = os.path.join(DATA_DIR, "total_grid.npy")

    excel_output_path = os.path.join(OUTPUT_DIR, "results.xlsx")
    image_output_path = os.path.join(OUTPUT_DIR, "coverage.png")

    print("📥 맵 데이터 로딩 중...")
    layer_grid = np.load(layer_grid_path)
    installable_grid = np.load(installable_grid_path)
    ignore_grid = np.load(ignore_grid_path)
    total_grid = np.load(total_grid_path)
    print("✅ 맵 데이터 로딩 완료")
    print("🕒 현재 시간:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    H, W = total_grid.shape
    print("layer_grid:", layer_grid.shape)
    print("installable_grid:", installable_grid.shape)
    print("ignore_grid:", ignore_grid.shape)
    print("total_grid:", total_grid.shape)

    print("📌 설치 가능 위치 및 커버리지 셀 계산 중...")
    candidate_positions = [(x, y) for y in range(H) for x in range(W)
                           if installable_grid[y, x] == 1]

    candidate_positions = candidate_positions[::3]

    grid_cells = [(x, y) for y in range(H) for x in range(W)
                  if total_grid[y, x] == 1 and ignore_grid[y, x] == 0]

    cell_heights = {(x, y): layer_grid[y, x] for y in range(H) for x in range(W)}
    print(f"✅ 후보 위치 수: {len(candidate_positions)}, 평가 셀 수: {len(grid_cells)}")

    def camera_factory(pos, theta):
        return Camera(position=pos, fov=60, direction=theta, range_limit=40)

    print("🚀 최적화 시작 (Greedy + LAHC)...")
    global_start = datetime.datetime.now()

    greedy_start = datetime.datetime.now()
    initial_cameras, initial_coverage = greedy_placement(
        candidate_positions,
        grid_cells,
        cell_heights,
        layer_grid,
        ignore_grid,
        camera_factory,
        coverage_threshold=0.95,
        total_grid=total_grid,
        top_k=1,
        min_ratio=0.5,
        frame_dir=FRAME_DIR
    )
    greedy_end = datetime.datetime.now()
    greedy_elapsed = (greedy_end - greedy_start).total_seconds()

    print(f"✅ Greedy 완료 — 카메라 수: {len(initial_cameras)}, "
          f"커버리지: {len(initial_coverage)} / {len(grid_cells)} "
          f"({len(initial_coverage)/len(grid_cells):.2%}), "
          f"소요 시간: {greedy_elapsed:.2f}초")

    remaining_time = 59 - greedy_elapsed
    if remaining_time <= 0:
        print("⚠️ Greedy에서 이미 59초 초과 → LAHC 생략")
        final_cameras, final_coverage, log = initial_cameras, initial_coverage, {}
    else:
        final_cameras, final_coverage, log = optimize_camera_placement(
            initial_cameras,
            initial_coverage,
            candidate_positions,
            grid_cells,
            cell_heights,
            layer_grid,
            ignore_grid,
            camera_factory,
            lahc_angle_step=10,
            lahc_history=100,
            total_time_limit=remaining_time,
            seed=42
        )

    global_end = datetime.datetime.now()
    print("✅ 최적화 완료")
    print(f"🕒 전체 최적화 수행 시간: {global_end - global_start}")

    print("📁 결과 저장 중 (엑셀 + 이미지)...")
    save_results_to_excel(final_cameras, final_coverage, log, excel_output_path)

    coverage_count = Counter()
    for cam in final_cameras:
        vis = cam.get_coverage(grid_cells, cell_heights, layer_grid, ignore_grid)
        for c in vis:
            coverage_count[c] += 1

    plot_coverage_map(
        grid_cells, final_cameras, final_coverage, ignore_grid,
        image_output_path, total_grid, coverage_count=coverage_count
    )
    print("✅ 결과 저장 완료")

    print(f"📊 최종 커버리지: {len(final_coverage) / len(grid_cells):.2%}")
    print(f"📸 설치된 카메라 수: {len(final_cameras)}")


if __name__ == "__main__":
    main()
