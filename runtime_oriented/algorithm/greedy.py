import os
import numpy as np
import datetime
from collections import Counter
from output.plotter import plot_coverage_map
from coverage.evaluator import compute_coverage

def precompute_sector_masks(radius, fov_deg=60, thetas=tuple(range(0, 360, 60))):
    masks = {}
    yy, xx = np.mgrid[-radius:radius+1, -radius:radius+1]
    coords = np.stack([xx.ravel(), yy.ravel()], axis=1)
    dist = np.hypot(coords[:,0], coords[:,1])
    inside_r = dist <= radius
    half = np.deg2rad(fov_deg) / 2

    for theta in thetas:
        rad = np.deg2rad(theta)
        cos_t, sin_t = np.cos(rad), np.sin(rad)
        dot = coords[:,0]*cos_t + coords[:,1]*sin_t
        ang = np.arccos(dot / (dist + 1e-9))
        inside_ang = ang <= half
        masks[theta] = coords[inside_r & inside_ang].astype(np.int32)
    return masks


def fast_valid_ratio_and_score(pos, theta, map_mask, score_mask, sector_masks, min_fov_ratio=0.5):
    H, W = map_mask.shape
    rel = sector_masks[theta]
    coords = rel + np.array(pos, dtype=np.int32)

    m = (coords[:,0] >= 0) & (coords[:,0] < W) & (coords[:,1] >= 0) & (coords[:,1] < H)
    if not np.any(m):
        return 0.0, 0

    cx = coords[m][:,0]
    cy = coords[m][:,1]
    total = rel.shape[0]

    valid_ratio = float(map_mask[cy, cx].sum()) / float(total)

    if valid_ratio < min_fov_ratio:
        return 0.0, 0

    abs_score = int(score_mask[cy, cx].sum())
    return valid_ratio, abs_score


def greedy_placement(
    candidate_positions,
    grid_cells,
    cell_heights,
    layer_grid,
    ignore_grid,
    camera_factory,
    coverage_threshold=0.96,
    total_grid=None,
    *,
    angle_step=60,
    top_k=1,
    min_ratio=0.5,
    cam_fov_deg=60,
    cam_range=40,
    save_final_only=True,
    frame_dir=None,
    stop_when_no_gain=True,
    downsample_step=1,
):
    if frame_dir is None:
        frame_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "frames")
    os.makedirs(frame_dir, exist_ok=True)

    if downsample_step > 1:
        candidate_positions = candidate_positions[::downsample_step]
    print(f"📉 후보 위치 수(다운샘플링 적용): {len(candidate_positions)}")

    placed_cameras = []
    covered_cells = set()
    remaining_positions = candidate_positions.copy()

    iteration = 0
    total_candidates = len(candidate_positions)

    thetas = tuple(range(0, 360, angle_step))
    sector_masks = precompute_sector_masks(radius=cam_range, fov_deg=cam_fov_deg, thetas=thetas)

    if total_grid is None:
        raise ValueError("total_grid (맵 마스크)가 필요합니다.")
    map_mask = (total_grid.astype(np.uint8) == 1)
    usable_mask = (total_grid.astype(np.uint8) == 1) & (ignore_grid.astype(np.uint8) == 0)

    coverage_cache = {}
    def get_cached_coverage(cam):
        key = (cam.position[0], cam.position[1], cam.direction)
        cov = coverage_cache.get(key)
        if cov is None:
            cov = set(cam.get_coverage(grid_cells, cell_heights, layer_grid, ignore_grid))
            coverage_cache[key] = cov
        return cov

    total_dir_checked = 0
    filtered_by_ratio = 0
    kept_for_scoring = 0
    evaluated_dirs = 0

    while True:
        uncovered_mask = np.zeros_like(map_mask, dtype=bool)
        for (x, y) in grid_cells:
            if (x, y) not in covered_cells:
                uncovered_mask[y, x] = True
        uncovered_mask &= usable_mask

        best_gain = 0
        best_camera = None
        best_position = None

        print(f"\n🔁 Greedy Iteration {iteration + 1} — 현재 커버리지: {len(covered_cells)} / {len(grid_cells)} ({len(covered_cells) / len(grid_cells):.2%})")

        for i, pos in enumerate(remaining_positions):
            dir_scores = []
            for theta in thetas:
                total_dir_checked += 1

                vr, approx_new = fast_valid_ratio_and_score(
                    pos, theta, map_mask, uncovered_mask, sector_masks, min_fov_ratio=0.5
                )
                if vr < min_ratio:
                    filtered_by_ratio += 1
                    continue
                kept_for_scoring += 1
                dir_scores.append((theta, approx_new))

            if not dir_scores:
                continue

            dir_scores.sort(key=lambda x: x[1], reverse=True)
            selected = dir_scores[:top_k]
            evaluated_dirs += len(selected)

            for theta, approx_score in selected:
                cam = camera_factory(pos, theta)
                vis = get_cached_coverage(cam)
                gain = len(vis) - len(vis & covered_cells)

                if i % 200 == 0:
                    print(f"   ▶ 후보 {i + 1}/{total_candidates} | θ={theta}° | approx_new={approx_score} | NEW={gain}")

                if gain > best_gain:
                    best_gain = gain
                    best_camera = cam
                    best_position = pos

        if best_camera is None:
            print("⚠️ 더 이상 유의미한 카메라 없음. 종료.")
            break

        if stop_when_no_gain and best_gain <= 0:
            print("⛳ 새로 덮을 셀이 더 이상 없음 → 조기 종료")
            break

        placed_cameras.append(best_camera)
        covered_cells.update(get_cached_coverage(best_camera))
        remaining_positions.remove(best_position)

        coverage_ratio = len(covered_cells) / len(grid_cells)
        print(f"✅ 카메라 #{len(placed_cameras)} 배치 완료 | 누적 커버리지: {len(covered_cells)} / {len(grid_cells)} ({coverage_ratio:.2%})")

        if coverage_ratio >= coverage_threshold:
            print("🎯 목표 커버리지 도달. Greedy 종료.")
            break

        iteration += 1

    if total_grid is not None:
        final_path = os.path.join(frame_dir, "greedy_final.png")
        coverage_count = Counter()
        for cam in placed_cameras:
            for c in get_cached_coverage(cam):
                coverage_count[c] += 1

        plot_coverage_map(
            grid_cells, placed_cameras, covered_cells, ignore_grid,
            final_path, total_grid, coverage_count=coverage_count
        )
        print(f"📸 Greedy 최종 시각화 저장 완료: {final_path}")

    print("\n📊 Pre-filter 통계")
    print(f" - 전체 방향 후보 수: {total_dir_checked}")
    print(f" - ratio 미달로 탈락: {filtered_by_ratio}")
    print(f" - ratio 통과(점수 산정): {kept_for_scoring}")
    print(f" - 실제 coverage 평가(top_k 적용): {evaluated_dirs}")
    print(f" - coverage cache 크기: {len(coverage_cache)}")

    return placed_cameras, covered_cells


print("🕒 현재 시간:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
