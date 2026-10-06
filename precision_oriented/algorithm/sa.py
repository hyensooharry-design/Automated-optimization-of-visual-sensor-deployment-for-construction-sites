# sa.py (revised)
import os
import re
import random
import math
from collections import Counter
from coverage.evaluator import compute_coverage
from output.plotter import plot_coverage_map  # 시각화 재사용

def _next_frame_index(frame_dir: str) -> int:
    os.makedirs(frame_dir, exist_ok=True)
    nums = []
    for f in os.listdir(frame_dir):
        m = re.match(r"frame_(\d{3})\.png$", f)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1

def simulated_annealing(
    initial_cameras,
    candidate_positions,
    grid_cells,
    cell_heights,
    layer_grid,
    ignore_grid,
    camera_factory,
    *,
    max_iter=300,
    frame_dir=None,
    total_grid=None,
    angle_step=10,               # 각도 전수 탐색 간격
    samples_per_step=64,         # Move 시 랜덤 후보 위치 샘플 수
    rotate_only_prob=0.25,       # 이웃: 회전만
    swap_prob=0.20,              # 이웃: 스왑
    initial_temp=120.0,
    cooling_rate=0.975,
    save_every=20,
    reheat_after=60,             # 개선 없는 스텝이 이 값에 도달하면 재가열
    reheat_factor=1.25,          # 재가열 배수
    seed=42                      # 재현성 옵션
):
    """
    전역형(move-only) SA (강화판)
      - 센서 수 고정(ADD/REMOVE 없음)
      - 이웃: Rotate-only / Move+Rotate / Swap+Reopt
      - Move는 후보 위치를 samples_per_step개 샘플링 후 그중 최선 선택
      - 각 카메라는 0~360을 angle_step 간격으로 전수 탐색하여 θ 최적화
      - 목표 커버리지 없이 best-so-far 최대화
    """
    if seed is not None:
        random.seed(seed)

    if frame_dir is None:
        frame_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "frames")
    os.makedirs(frame_dir, exist_ok=True)

    # ---------- 초기 상태 ----------
    current_cameras = list(initial_cameras)  # Camera 인스턴스
    current_coverage = compute_coverage(current_cameras, grid_cells, cell_heights, layer_grid, ignore_grid)

    best_cameras = list(current_cameras)
    best_coverage = set(current_coverage)

    next_idx = _next_frame_index(frame_dir)
    saved_frames = 0
    log = []
    temp = float(initial_temp)
    stall = 0
    total_cells = len(grid_cells) or 1

    # ---------- 유틸 ----------
    def _coverage_count(cams):
        cnt = Counter()
        for cam in cams:
            vis = cam.get_coverage(grid_cells, cell_heights, layer_grid, ignore_grid)
            for c in vis:
                cnt[c] += 1
        return cnt

    def _reopt_single(base_cams, pos):
        """주어진 pos에서 각도 전수 탐색으로 최선 카메라 구성 반환"""
        base_cov = compute_coverage(base_cams, grid_cells, cell_heights, layer_grid, ignore_grid)
        best_theta, best_cov, best_gain = None, None, -1e18
        for theta in range(0, 360, angle_step):
            test_cam = camera_factory(pos, theta)
            vis = test_cam.get_coverage(grid_cells, cell_heights, layer_grid, ignore_grid)
            union_cov = base_cov | vis
            gain = len(union_cov) - len(base_cov)  # ▲ base 대비 순증가
            if gain > best_gain:
                best_gain = gain
                best_theta = theta
                best_cov = union_cov
        return best_theta, best_cov

    def _rotate_only(idx):
        """카메라 idx: 위치 고정, θ만 재탐색"""
        other = [c for i, c in enumerate(current_cameras) if i != idx]
        anchor = current_cameras[idx].position
        theta, cov = _reopt_single(other, anchor)
        neighbor = list(other) + [camera_factory(anchor, theta)]
        return neighbor, cov

    def _move_and_rotate(idx):
        """카메라 idx: 다른 후보 위치로 이동 + θ 최적화"""
        used = {cam.position for i, cam in enumerate(current_cameras) if i != idx}
        pool = list(set(candidate_positions) - used)
        if not pool:
            return None, None
        if len(pool) > samples_per_step:
            pool = random.sample(pool, samples_per_step)

        other = [c for i, c in enumerate(current_cameras) if i != idx]
        base_cov = compute_coverage(other, grid_cells, cell_heights, layer_grid, ignore_grid)

        best_pos, best_theta, best_cov, best_gain = None, None, None, -1e18
        for pos in pool:
            for theta in range(0, 360, angle_step):
                test_cam = camera_factory(pos, theta)
                vis = test_cam.get_coverage(grid_cells, cell_heights, layer_grid, ignore_grid)
                union_cov = base_cov | vis
                gain = len(union_cov) - len(base_cov)  # ▲ 로컬 기준으로 비교 (중요 수정)
                if gain > best_gain:
                    best_gain = gain
                    best_pos, best_theta, best_cov = pos, theta, union_cov

        if best_pos is None:
            return None, None
        neighbor = list(other) + [camera_factory(best_pos, best_theta)]
        return neighbor, best_cov

    def _swap_and_reopt(i, j):
        """
        카메라 i, j의 '위치'를 실제로 스왑한 뒤,
        두 위치 각각에서 전수 탐색으로 θ 재최적화 (순차적으로)
        """
        if i == j:
            return None, None

        cams = list(current_cameras)
        pos_i, pos_j = cams[i].position, cams[j].position
        others = [c for k, c in enumerate(cams) if k not in (i, j)]

        # 1) j가 pos_i로 간다고 가정하고 pos_i에서 최적 θ
        theta_j_at_i, cov_after_j = _reopt_single(others, pos_i)
        cams_after_j = others + [camera_factory(pos_i, theta_j_at_i)]

        # 2) i가 pos_j로 간다고 가정하고 pos_j에서 최적 θ (이미 pos_i에 j가 앉은 상태에서)
        theta_i_at_j, cov_final = _reopt_single(cams_after_j, pos_j)

        neighbor = cams_after_j + [camera_factory(pos_j, theta_i_at_j)]

        # 안전하게 최종 커버리지를 재계산(셋 형태 보장)
        n_cov = compute_coverage(neighbor, grid_cells, cell_heights, layer_grid, ignore_grid)
        return neighbor, n_cov

    # ---------- 메인 루프 ----------
    for step in range(max_iter):
        if not candidate_positions or not current_cameras:
            break

        # 이웃 유형 선택
        r = random.random()
        if r < rotate_only_prob:
            move_type = "rotate"
            idx = random.randrange(len(current_cameras))
            neighbor, n_cov = _rotate_only(idx)
        elif r < rotate_only_prob + swap_prob and len(current_cameras) >= 2:
            move_type = "swap"
            i, j = random.sample(range(len(current_cameras)), 2)
            neighbor, n_cov = _swap_and_reopt(i, j)
        else:
            move_type = "move"
            idx = random.randrange(len(current_cameras))
            neighbor, n_cov = _move_and_rotate(idx)

        if neighbor is None or n_cov is None:
            stall += 1
            temp *= cooling_rate
            continue

        delta = len(n_cov) - len(current_coverage)
        accept = (delta > 0) or (math.exp(delta / max(temp, 1e-12)) > random.random())

        if accept:
            current_cameras = neighbor
            current_coverage = n_cov
            if len(current_coverage) > len(best_coverage):
                best_cameras = list(current_cameras)
                best_coverage = set(current_coverage)
                stall = 0
            else:
                stall += 1
        else:
            stall += 1

        cov_ratio = len(current_coverage) / total_cells
        log.append({
            "step": step,
            "move": move_type,
            "temperature": round(temp, 4),
            "camera_count": len(current_cameras),
            "coverage": len(current_coverage),
            "coverage_ratio": round(cov_ratio * 100, 2),
            "accepted": bool(accept),
        })

        # 중간 프레임 저장 (step=0 포함 → 의도대로면 OK)
        if (save_every is not None) and (step % save_every == 0) and (total_grid is not None):
            frame_path = os.path.join(frame_dir, f"frame_{(next_idx + saved_frames):03d}.png")
            plot_coverage_map(
                grid_cells, current_cameras, current_coverage, ignore_grid,
                frame_path, total_grid, coverage_count=_coverage_count(current_cameras)
            )
            saved_frames += 1

        # 냉각 & 정체 시 재가열
        temp *= cooling_rate
        if stall >= reheat_after:
            temp *= reheat_factor
            stall = 0

    # ---------- 최종 프레임(최고해) ----------
    if total_grid is not None:
        final_path = os.path.join(frame_dir, f"frame_{(next_idx + saved_frames):03d}.png")
        plot_coverage_map(
            grid_cells, best_cameras, best_coverage, ignore_grid,
            final_path, total_grid, coverage_count=_coverage_count(best_cameras)
        )

    return best_cameras, best_coverage, log
