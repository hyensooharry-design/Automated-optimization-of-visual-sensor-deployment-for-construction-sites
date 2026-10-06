from pathlib import Path


def make_video_from_frames(frame_dir, output_path, fps=1):
    """Create an MP4 from PNG frames in frame_dir, ordered by filename."""
    import imageio.v2 as imageio

    frames = sorted(Path(frame_dir).glob("frame_*.png"))
    if not frames:
        raise FileNotFoundError(f"No PNG frames found in: {frame_dir}")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(output, fps=fps) as writer:
        for frame in frames:
            writer.append_data(imageio.imread(frame))
