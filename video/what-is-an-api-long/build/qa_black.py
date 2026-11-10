import subprocess, sys, numpy as np
src = sys.argv[1]; W, H = 480, 270   # downscaled decode; patches scaled
cmd = ["ffmpeg", "-loglevel", "error", "-i", src, "-vf", f"fps=0.5,scale={W}:{H},format=rgb24", "-f", "rawvideo", "-"]
raw = subprocess.run(cmd, capture_output=True).stdout
n = len(raw) // (W * H * 3); fr = np.frombuffer(raw[: n * W * H * 3], np.uint8).reshape(n, H, W, 3)
# corners 10x10 px (=40x40 at 1080p) and left/right edge strips (15 px = 60 px at 1920 width) excluding the top HUD strip rows (y<22) which holds the progress bar
bad = 0
for i, f in enumerate(fr):
    patches = [f[H-10:, :10], f[H-10:, W-10:], f[:10, :10], f[:10, W-10:]]
    strips = [f[22:, :15], f[22:, W-15:]]
    for p in patches + strips:
        if p.reshape(-1, 3).mean(0).max() > 10:
            bad += 1; print("bright patch in frame", i, "t=", i * 2, "s", p.reshape(-1,3).mean(0)); break
print("frames checked", n, "bad", bad)
