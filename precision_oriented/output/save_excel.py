import pandas as pd

def save_results_to_excel(cameras, covered_cells, log, filename):
    camera_data = [{
        "x": cam.position[0],
        "y": cam.position[1],
        "fov": cam.fov,
        "direction": cam.direction,
        "range": cam.range_limit
    } for cam in cameras]

    camera_df = pd.DataFrame(camera_data)
    coverage_df = pd.DataFrame(list(covered_cells), columns=["x", "y"])
    log_df = pd.DataFrame([log]) if isinstance(log, dict) else pd.DataFrame(log)

    with pd.ExcelWriter(filename) as writer:
        camera_df.to_excel(writer, sheet_name="Cameras", index=False)
        coverage_df.to_excel(writer, sheet_name="Coverage", index=False)
        log_df.to_excel(writer, sheet_name="Log", index=False)

    print(f"📁 결과 저장 완료: {filename}")