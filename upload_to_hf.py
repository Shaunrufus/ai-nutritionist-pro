"""
Upload AI Nutritionist files to Hugging Face Space.
Run: python upload_to_hf.py <YOUR_HF_TOKEN>
Get your token at: https://huggingface.co/settings/tokens
"""
import sys
import os
from pathlib import Path
from huggingface_hub import HfApi

# ── Config ────────────────────────────────────
REPO_ID   = "shaunrufus14/ai-nutritionist-pro"
REPO_TYPE = "space"
PROJECT   = Path(__file__).resolve().parent

# Files to upload: (local_path, path_in_repo)
FILES = [
    (PROJECT / "app.py",           "app.py"),
    (PROJECT / "requirements.txt", "requirements.txt"),
    (PROJECT / "README.md",        "README.md"),
    (PROJECT / "config.py",        "config.py"),
]

# Also upload the ML model if it exists
MODEL = PROJECT / "models" / "nutrition_regressor.pkl"
if MODEL.exists():
    FILES.append((MODEL, "models/nutrition_regressor.pkl"))
    print(f"[OK] Found ML model: {MODEL}")
else:
    print(f"[WARN] ML model not found at {MODEL} - skipping")

# ── Token ─────────────────────────────────────
if len(sys.argv) > 1:
    token = sys.argv[1]
else:
    token = os.getenv("HF_TOKEN")

if not token:
    print("No HF token provided!")
    print("Usage: python upload_to_hf.py <YOUR_HF_TOKEN>")
    print("Get your token: https://huggingface.co/settings/tokens")
    sys.exit(1)

# ── Upload ────────────────────────────────────
api = HfApi(token=token)

print(f"\nUploading to: https://huggingface.co/spaces/{REPO_ID}\n")

for local, remote in FILES:
    if not Path(local).exists():
        print(f"[SKIP] Not found: {local}")
        continue
    print(f"[UPLOAD] {remote}...", end=" ", flush=True)
    try:
        api.upload_file(
            path_or_fileobj=str(local),
            path_in_repo=remote,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            commit_message=f"Upload {remote}",
        )
        print("OK")
    except Exception as e:
        print(f"FAILED: {e}")

print(f"\nDone! Your app should be live at:")
print(f"   https://huggingface.co/spaces/{REPO_ID}")
print(f"\nWait 2-3 minutes for the Space to build and start.")
