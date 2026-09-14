import hashlib
import json
from pathlib import Path
from PIL import Image
from engine import ROOT
from exercise_media import load_manifest,image_paths
from prepare_data import key

def test_local_demonstrations_match_catalogue():
    import pandas as pd
    items=pd.read_csv(ROOT/'data/processed/exercises.csv').set_index('exercise_id')
    manifest=load_manifest()
    assert len(manifest)==24
    for eid,entry in manifest.items():
        assert key(entry['source_name'])==key(items.loc[eid,'name'])
        paths=image_paths(eid,manifest)
        assert len(paths)==len(entry['images'])==2
        for path,metadata in zip(paths,entry['images']):
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==metadata['sha256']
            with Image.open(path) as im: im.verify()
    # A related name is not permission to attach a different exercise's photo.
    assert image_paths('ex_bearcrawl',manifest)==[]

def test_media_missing_files_and_path_escape():
    assert image_paths('missing',{})==[]
    assert image_paths('x',{'x':{'images':[{'path':'README.md'},{'path':'data/images/no-file.jpg'}]}})==[]
