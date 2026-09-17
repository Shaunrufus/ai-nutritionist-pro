"""
Upload all AI Nutritionist files to GitHub via Contents API.
Works without 'repo' scope - uses direct file API.
"""
import sys, os, base64, requests, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

TOKEN = os.environ.get('GITHUB_TOKEN', '')
REPO  = 'Shaunrufus/ai-nutritionist-pro'
BASE  = Path(r'c:\Users\Kalurieshaun.Rufus\.gemini\antigravity-ide\scratch\AI-Nutritionist')
HEADERS = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'Content-Type': 'application/json'
}

# Files to upload (local path relative to BASE, remote path in repo)
FILES = [
    ('app/Streamlit_app.py',           'app/Streamlit_app.py'),
    ('app/Streamlit_app.py',           'app/streamlit_app.py'),
    ('streamlit_app.py',               'streamlit_app.py'),
    ('streamlit_app.py',               'Streamlit_app.py'),
    ('app/auth.py',                    'app/auth.py'),
    ('app/vision_tracker.py',          'app/vision_tracker.py'),
    ('app/daily_space.py',             'app/daily_space.py'),
    ('app/__init__.py',                'app/__init__.py'),
    ('app.py',                          'app.py'),
    ('config.py',                       'config.py'),
    ('requirements.txt',               'requirements.txt'),
    ('README.md',                       'README.md'),
    ('.gitignore',                      '.gitignore'),
    ('.env.example',                    '.env.example'),
    ('.streamlit/config.toml',          '.streamlit/config.toml'),
    ('.streamlit/secrets.toml.example', '.streamlit/secrets.toml.example'),
    ('setup.py',                        'setup.py'),
    ('models/nutrition_regressor.pkl',  'models/nutrition_regressor.pkl'),
]

def upload_file(local_rel, remote_path):
    local = BASE / local_rel
    if not local.exists():
        print(f'  [SKIP] Not found: {local_rel}')
        return False

    with open(local, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode('utf-8')

    url = f'https://api.github.com/repos/{REPO}/contents/{remote_path}'

    # Check if file already exists (need sha to update)
    r = requests.get(url, headers=HEADERS, timeout=15)
    sha = r.json().get('sha') if r.status_code == 200 else None

    payload = {
        'message': f'Upload {remote_path}',
        'content': content_b64,
        'branch': 'main'
    }
    if sha:
        payload['sha'] = sha

    r2 = requests.put(url, headers=HEADERS, json=payload, timeout=30)
    if r2.status_code in (200, 201):
        print(f'  [OK] {remote_path}')
        return True
    else:
        print(f'  [FAIL] {remote_path}: {r2.status_code} {r2.json().get("message", "")}')
        return False

print(f'\nUploading to: https://github.com/{REPO}\n')
ok, fail = 0, 0
for local_rel, remote_path in FILES:
    if upload_file(local_rel, remote_path):
        ok += 1
    else:
        fail += 1

print(f'\nDone: {ok} uploaded, {fail} failed/skipped')
print(f'Repo: https://github.com/{REPO}')
