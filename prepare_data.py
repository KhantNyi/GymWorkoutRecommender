"""Normalize the Kaggle catalogue and enrich exact title matches with instructions."""
import json
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent

def key(value):
    return re.sub(r'[^a-z0-9]', '', str(value).lower())

def main():
    raw, out = ROOT / 'data/raw', ROOT / 'data/processed'
    out.mkdir(parents=True, exist_ok=True)
    original = pd.read_csv(raw / 'megaGymDataset.csv')
    df = original.rename(columns={'Title':'name','Desc':'description','Type':'category',
        'BodyPart':'muscle','Equipment':'equipment','Level':'level','Rating':'source_rating'})
    df = df.dropna(subset=['name']).copy()
    df['name'] = df.name.str.strip()
    df['match_key'] = df.name.map(key)
    df = df[df.match_key.ne('')].drop_duplicates('match_key').copy()
    for col in ['description','category','muscle','equipment','level']:
        df[col] = df[col].fillna('unknown').str.strip().str.lower()
    df['equipment'] = df.equipment.replace({'body only':'bodyweight','e-z curl bar':'ez bar'})
    df['source_rating'] = pd.to_numeric(df.source_rating, errors='coerce').where(lambda s:s.between(0,10))
    db = {key(e['name']):e for e in json.loads((raw/'exercises.json').read_text(encoding='utf-8'))}
    df['instructions'] = df.match_key.map(lambda k:'\n'.join(db.get(k,{}).get('instructions',[])))
    df['instruction_source'] = df.instructions.map(lambda s:'free-exercise-db (exact normalized title)' if s else '')
    df['exercise_id'] = df.match_key.map(lambda k: 'ex_' + k)
    # Source equipment is incomplete. Add explicitly mentioned accessories conservatively.
    def requirements(row):
        required = {row.equipment}
        text = row['name'].lower() + ' ' + row.description
        for token in ['bench','pull-up bar','cable','dumbbell','barbell','kettlebell','bands']:
            if token in text:
                required.add({'pull-up bar':'pullup bar','cable':'cable','dumbbell':'dumbbell',
                              'barbell':'barbell','kettlebell':'kettlebells'}.get(token,token))
        if 'partner' in text: required.add('partner')
        return '|'.join(sorted(required))
    df['required_equipment'] = df.apply(requirements,axis=1)
    cols=['exercise_id','name','description','category','muscle','equipment','required_equipment',
          'level','source_rating','instructions','instruction_source']
    df[cols].to_csv(out/'exercises.csv',index=False)
    members=pd.read_csv(raw/'gym_members_exercise_tracking.csv').drop_duplicates()
    members.to_csv(out/'members.csv',index=False)
    report={'raw_exercises':len(original),'clean_exercises':len(df),
            'removed_duplicate_or_missing_titles':len(original)-len(df),
            'instruction_matches':int(df.instructions.ne('').sum()),'member_rows':len(members),
            'missing_source_ratings':int(df.source_rating.isna().sum()),
            'equipment_counts':df.equipment.value_counts().to_dict(),
            'level_counts':df.level.value_counts().to_dict()}
    (ROOT/'reports/data_quality.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
