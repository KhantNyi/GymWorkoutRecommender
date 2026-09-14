"""Download a bounded selection of exact-match exercise demonstrations."""
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote
import hashlib
import io
import json
import pandas as pd
from PIL import Image
from prepare_data import key

ROOT = Path(__file__).resolve().parent
PRIORITY = ['Pushups','Crunches','Reverse_Crunch','Plank','Bodyweight_Squat',
            'Dumbbell_Squat','Goblet_Squat','Dumbbell_Lunges','Barbell_Squat',
            'Barbell_Bench_Press_-_Medium_Grip','Dumbbell_Bench_Press',
            'Dumbbell_Bicep_Curl','Hammer_Curls','Barbell_Curl','Pullups',
            'Incline_Push-Up','Standing_Calf_Raises','Dumbbell_Shoulder_Press',
            'Side_Lateral_Raise','Seated_Cable_Rows','Superman','Mountain_Climbers',
            'Jumping_Jacks','Butt_Lift_Bridge']

def main():
    source=json.loads((ROOT/'data/raw/exercises.json').read_text(encoding='utf-8'))
    lookup={key(e['name']): e for e in source}
    items=pd.read_csv(ROOT/'data/processed/exercises.csv').fillna('')
    candidates=[(r,lookup[key(r['name'])]) for _,r in items.iterrows()
                if key(r['name']) in lookup and lookup[key(r['name'])].get('images')]
    selected=[(r,e) for r,e in candidates if e['id'] in PRIORITY]
    # Fill the remaining slots with beginner demonstrations from the same source.
    for r,e in candidates:
        if len(selected)>=24: break
        if r['level']=='beginner' and e['id'] not in {v['id'] for _,v in selected}:
            selected.append((r,e))
    target=ROOT/'data/images'; target.mkdir(exist_ok=True)
    entries={}; failures=[]
    for row,exercise in selected[:24]:
        images=[]
        for i,remote in enumerate(exercise['images'][:2]):
            url='https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/'+quote(remote,safe='/')
            dest=target/f"{row['exercise_id']}_{i}.jpg"
            try:
                payload=dest.read_bytes() if dest.exists() else urlopen(Request(url,headers={'User-Agent':'GymWorkoutCourseProject/1.0'}),timeout=20).read()
                with Image.open(io.BytesIO(payload)) as im: im.verify()
                if not dest.exists(): dest.write_bytes(payload)
                images.append({'path':dest.relative_to(ROOT).as_posix(),'url':url,
                               'sha256':hashlib.sha256(payload).hexdigest()})
            except Exception as exc:
                failures.append({'exercise':row['name'],'error':str(exc)})
        if images:
            entries[row['exercise_id']]={'exercise_name':row['name'],'source_name':exercise['name'],
                'source':'Free Exercise DB','source_url':'https://github.com/yuhonas/free-exercise-db',
                'license':'Unlicense / public domain dedication; see data/raw/FREE_EXERCISE_LICENSE.md',
                'match':'exact normalized exercise name','images':images}
    if not entries: raise RuntimeError('No exercise images downloaded: '+str(failures[:2]))
    (target/'manifest.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
    print(f'Downloaded demonstrations for {len(entries)} exercises ({sum(len(e["images"]) for e in entries.values())} images).')
    if failures: print(f'{len(failures)} image requests failed; successful images retained.')

if __name__=='__main__': main()
