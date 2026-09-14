"""Only attach locally verified images to their exact catalogue exercise."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def load_manifest():
    path=ROOT/'data/images/manifest.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

def image_paths(exercise_id, manifest):
    paths=[]
    for image in manifest.get(exercise_id,{}).get('images',[]):
        path=(ROOT/image['path']).resolve()
        if path.is_relative_to(ROOT/'data/images') and path.is_file(): paths.append(str(path))
    return paths
