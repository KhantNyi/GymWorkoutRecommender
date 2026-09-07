"""Download original public datasets; retain archives, metadata and SHA-256 hashes."""
from pathlib import Path
import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
SOURCES = [
    ('gym_exercises.zip', 'https://www.kaggle.com/api/v1/datasets/download/niharika41298/gym-exercise-data'),
    ('gym_members.zip', 'https://www.kaggle.com/api/v1/datasets/download/valakhorasani/gym-members-exercise-dataset'),
    ('exercises.json', 'https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json'),
    ('FREE_EXERCISE_LICENSE.md', 'https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/LICENSE.md'),
    ('gym_exercises_metadata.json', 'https://www.kaggle.com/api/v1/datasets/list/niharika41298/gym-exercise-data'),
    ('gym_members_metadata.json', 'https://www.kaggle.com/api/v1/datasets/list/valakhorasani/gym-members-exercise-dataset'),
]

def main():
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, url in SOURCES:
        path = raw / name
        data = path.read_bytes() if path.exists() else urllib.request.urlopen(
            urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read()
        if name.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for item in archive.infolist():
                    if item.filename.lower().endswith('.csv'):
                        (raw / Path(item.filename).name).write_bytes(archive.read(item))
        elif name.endswith('.json'):
            json.loads(data)  # Reject login pages and error HTML.
        path.write_bytes(data)
        manifest.append(dict(file=name, url=url, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                             verified_at=datetime.now(timezone.utc).isoformat()))
        print(f'{name}: {len(data):,} bytes', flush=True)
    (ROOT / 'data/source_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
