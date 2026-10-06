# visualizer.py
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# coverage_count: dict 또는 Counter {(x,y): 횟수}
def visualize_camera_map(grid, cameras, covered_cells=None, obstacle_cells=None, ignore_map=None,
                         grid_size=5.0, save_path=None, coverage_count=None):
    n_rows, n_cols = grid.shape
    grid_img = np.zeros((n_rows, n_cols, 3), dtype=np.uint8)

    for y in range(n_rows):
        for x in range(n_cols):
            if grid[y, x] == 0:
                if ignore_map is not None and ignore_map[y, x] == 1:
                    grid_img[y, x] = [160, 160, 160]
                else:
                    grid_img[y, x] = [0, 0, 0]
                continue

            if ignore_map is not None and ignore_map[y, x] == 1:
                grid_img[y, x] = [160, 160, 160]
                continue

            if obstacle_cells and (x, y) in obstacle_cells:
                grid_img[y, x] = [255, 255, 255]
                continue

            if covered_cells and (x, y) in covered_cells:
                if coverage_count is not None:
                    k = coverage_count.get((x, y), 1)
                    if k >= 2:
                        grid_img[y, x] = [135, 206, 235]
                    else:
                        grid_img[y, x] = [0, 255, 0]
                else:
                    grid_img[y, x] = [0, 255, 0]
            else:
                grid_img[y, x] = [255, 0, 0]

    for cam in cameras:
        x, y = cam.position
        if 0 <= y < n_rows and 0 <= x < n_cols:
            grid_img[y, x] = [255, 255, 0]

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(grid_img, origin='lower')

    for y in range(n_rows):
        for x in range(n_cols):
            rect = patches.Rectangle((x - 0.5, y - 0.5), 1, 1,
                                     linewidth=0.2, edgecolor='gray', facecolor='none')
            ax.add_patch(rect)

    legend_patches = [
        patches.Patch(color='red', label='Uncovered'),
        patches.Patch(color='green', label='Covered (k=1)'),
        patches.Patch(color=(135/255,206/255,235/255), label='Overlap (k≥2)'),
        patches.Patch(color='gray', label='Ignore'),
        patches.Patch(color='black', label='Outside'),
        patches.Patch(color='yellow', label='Camera'),
    ]
    ax.legend(handles=legend_patches, loc='upper right')
    ax.set_title("Sensor Coverage Visualization")
    ax.axis('off')

    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=300)
        print(f"✅ 시각화 저장 완료: {save_path}")
    plt.close()
