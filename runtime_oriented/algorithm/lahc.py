def lahc(
    initial_cameras,
    candidate_positions,
    grid_cells,
    cell_heights,
    layer_grid,
    ignore_grid,
    camera_factory,
    *,
    angle_step=10,
    deadline=None,
    L=100,
    seed=42,
    no_improve_limit=2000
):
    import time, random, math
    from coverage.evaluator import compute_coverage

    if seed is not None:
        random.seed(seed)

    current_cams = list(initial_cameras)
    current_cov = compute_coverage(current_cams, grid_cells, cell_heights, layer_grid, ignore_grid)

    best_cams = list(current_cams)
    best_cov = set(current_cov)
    last_best_iter = 0

    total_cells = len(grid_cells) or 1
    grid_set = set(grid_cells)

    history = [len(current_cov)] * L
    idx = 0

    it = 0
    log = []

    while True:
        if deadline is not None and time.time() >= deadline:
            break

        it += 1

        move_type = random.random()
        if move_type < 0.5:
            swap_idx = random.randrange(len(current_cams))
            other = [c for i, c in enumerate(current_cams) if i != swap_idx]
            pos = current_cams[swap_idx].position
            theta = random.randrange(0, 360, angle_step)
            new_cams = other + [camera_factory(pos, theta)]

        elif move_type < 0.8:
            swap_idx = random.randrange(len(current_cams))
            other = [c for i, c in enumerate(current_cams) if i != swap_idx]
            used = {c.position for c in other}
            pool = list(set(candidate_positions) - used)
            if not pool:
                continue
            pos = random.choice(pool)
            theta = random.randrange(0, 360, angle_step)
            new_cams = other + [camera_factory(pos, theta)]

        else:
            uncovered = list(grid_set - current_cov)
            if not uncovered:
                continue
            target_cell = random.choice(uncovered)
            tx, ty = target_cell
            swap_idx = random.randrange(len(current_cams))
            other = [c for i, c in enumerate(current_cams) if i != swap_idx]
            used = {c.position for c in other}
            pool = sorted(set(candidate_positions) - used, key=lambda p: (p[0]-tx)**2 + (p[1]-ty)**2)
            if not pool:
                continue
            pos = pool[0]
            theta = random.randrange(0, 360, angle_step)
            new_cams = other + [camera_factory(pos, theta)]

        new_cov = compute_coverage(new_cams, grid_cells, cell_heights, layer_grid, ignore_grid)
        new_score = len(new_cov)
        current_score = len(current_cov)

        accept = False
        if new_score >= current_score or new_score >= history[idx]:
            accept = True
        else:
            delta = new_score - current_score
            T = max(1, L / 10)
            prob = math.exp(delta / T) if delta < 0 else 1.0
            if random.random() < prob:
                accept = True

        if accept:
            current_cams = new_cams
            current_cov = new_cov

            if new_score > len(best_cov):
                best_cams = list(current_cams)
                best_cov = set(current_cov)
                last_best_iter = it

        history[idx] = len(current_cov)
        idx = (idx + 1) % L

        if it - last_best_iter > no_improve_limit:
            swap_idx = random.randrange(len(current_cams))
            other = [c for i, c in enumerate(current_cams) if i != swap_idx]
            used = {c.position for c in other}
            pool = list(set(candidate_positions) - used)
            if pool:
                pos = random.choice(pool)
                theta = random.randrange(0, 360, angle_step)
                current_cams[swap_idx] = camera_factory(pos, theta)
                current_cov = compute_coverage(current_cams, grid_cells, cell_heights, layer_grid, ignore_grid)
                print(f"🔄 Plateau escape at iter {it}")
            last_best_iter = it

        if it % 500 == 0:
            log.append({
                "iter": it,
                "coverage": len(current_cov),
                "coverage_ratio": round(len(current_cov) / total_cells * 100, 2),
                "best": len(best_cov)
            })

    print(f"⏱️ LAHC 종료 — 반복 {it}회, 최고 커버리지 {len(best_cov)}/{len(grid_cells)} "
          f"({len(best_cov)/total_cells:.2%})")

    return best_cams, best_cov, log
