"""Chapter-aligned recommendation algorithms with common hard constraints."""
from dataclasses import dataclass, field
from pathlib import Path
import math
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT=Path(__file__).resolve().parent
LEVELS={'beginner':0,'intermediate':1,'expert':2}
GOALS=['General Fitness','Weight Loss','Muscle Gain','Strength']
METHODS=['Hybrid','Content-based','Context-aware']
GOAL_TEXT={'General Fitness':'strength cardio endurance flexibility full body compound',
           'Weight Loss':'cardio endurance aerobic circuit full body',
           'Muscle Gain':'strength hypertrophy muscle compound isolation',
           'Strength':'strength powerlifting compound barbell'}

@dataclass
class Profile:
    user_id: str='local-user'
    age: int=25
    gender: str='Prefer not to say'
    height_cm: float=170
    weight_kg: float=70
    goal: str='General Fitness'
    experience: str='beginner'
    equipment: list=field(default_factory=lambda:['bodyweight','dumbbell','bench'])
    muscles: list=field(default_factory=list)
    excluded_muscles: list=field(default_factory=list)
    minutes: int=30
    location: str='Gym'
    energy: str='Normal'

    @property
    def bmi(self): return round(self.weight_kg/(self.height_cm/100)**2,1)

    def validate(self):
        if not self.user_id.strip() or len(self.user_id)>80: raise ValueError('Enter a user ID of 1–80 characters.')
        if self.goal not in GOALS or self.experience not in LEVELS: raise ValueError('Invalid goal or experience.')
        values=[self.age,self.height_cm,self.weight_kg,self.minutes]
        if not all(math.isfinite(float(v)) for v in values): raise ValueError('Profile values must be finite.')
        if not (18<=self.age<=100 and 100<=self.height_cm<=250 and 30<=self.weight_kg<=300 and 10<=self.minutes<=180):
            raise ValueError('Profile values are outside supported ranges.')
        if self.location not in ['Gym','Home','Outdoors'] or self.energy not in ['Low','Normal','High']:
            raise ValueError('Invalid context.')

class Recommender:
    def __init__(self, exercises=None, history=None):
        self.items=(pd.read_csv(ROOT/'data/processed/exercises.csv').fillna('') if exercises is None else exercises.copy()).reset_index(drop=True)
        self.history=history if history is not None else pd.DataFrame(columns=['user_id','exercise_id','rating','completion'])
        text=self.items[['name','description','category','muscle','level','equipment']].agg(' '.join,axis=1)
        self.vectorizer=TfidfVectorizer(stop_words='english',ngram_range=(1,2),min_df=1)
        self.features=self.vectorizer.fit_transform(text)
        self.ids=self.items.exercise_id.tolist()
        self.lookup={eid:i for i,eid in enumerate(self.ids)}

    def recommend(self,profile,method='Hybrid',top_n=8,exclude_seen=False):
        profile.validate()
        if method not in METHODS: raise ValueError('Unknown recommendation method.')
        if not isinstance(top_n,int) or not 1<=top_n<=100: raise ValueError('top_n must be 1–100.')
        df=self.items.copy()
        equipment=set(profile.equipment)|{'bodyweight'}
        if profile.location=='Outdoors': equipment-= {'machine','cable','smith machine'}
        limit=min(LEVELS[profile.experience],0 if profile.energy=='Low' else 2)
        allowed=df.level.map(LEVELS).fillna(99)<=limit
        allowed &= df.required_equipment.map(lambda s:set(s.split('|')).issubset(equipment))
        allowed &= ~df.muscle.isin(profile.excluded_muscles)
        if profile.muscles: allowed &= df.muscle.isin(profile.muscles)
        seen=self.history[self.history.user_id.eq(profile.user_id)]
        if exclude_seen: allowed &= ~df.exercise_id.isin(seen.exercise_id)
        query=GOAL_TEXT[profile.goal]+' '+' '.join(profile.muscles)
        q=self.vectorizer.transform([query])
        content=cosine_similarity(q,self.features)[0]
        positives=seen[pd.to_numeric(seen.rating,errors='coerce')>=4]
        indices=[self.lookup[i] for i in positives.exercise_id if i in self.lookup]
        if indices:
            content=.6*content+.4*cosine_similarity(np.asarray(self.features[indices].mean(axis=0)),self.features)[0]
        ratings=pd.to_numeric(df.source_rating,errors='coerce')
        prior=ratings.fillna(ratings.median() if ratings.notna().any() else 5).to_numpy()/10
        # Bayesian shrinkage on genuine app ratings, using the source score as prior.
        agg=self.history.groupby('exercise_id').rating.agg(['mean','count']) if not self.history.empty else pd.DataFrame(columns=['mean','count'])
        counts=df.exercise_id.map(agg['count']).fillna(0).to_numpy()
        averages=df.exercise_id.map(agg['mean']).fillna(0).to_numpy()/5
        popularity=(5*prior+counts*averages)/(5+counts)
        preferred={'Weight Loss':['cardio','plyometrics'],'Strength':['strength','powerlifting'],
                   'Muscle Gain':['strength'],'General Fitness':['strength','cardio','stretching']}[profile.goal]
        knowledge=.7*df.category.isin(preferred).to_numpy()+.3*df.level.eq(profile.experience).to_numpy()
        # Local feedback completion supplies a contextual preference signal.
        completion=seen.groupby('exercise_id').completion.mean() if not seen.empty else pd.Series(dtype=float)
        context=.6*knowledge+.4*df.exercise_id.map(completion).fillna(.5).to_numpy()
        scores={'Popularity':popularity,'Content-based':content,'Knowledge':knowledge,'Context-aware':context}
        scores['Hybrid']=.40*content+.20*popularity+.25*knowledge+.15*context
        df['score']=scores[method]
        for name,score in scores.items(): df[name]=score
        df=df[allowed].sort_values(['score','name'],ascending=[False,True])
        # Greedy diversity avoids filling a full-body session with one muscle group.
        selected=[]; muscle_counts={}
        while len(df) and len(selected)<top_n:
            adjusted=df.score-df.muscle.map(lambda m:.10*muscle_counts.get(m,0))
            idx=adjusted.idxmax(); row=df.loc[idx].copy(); selected.append(row)
            muscle_counts[row.muscle]=muscle_counts.get(row.muscle,0)+1
            df=df.drop(idx)
        result=pd.DataFrame(selected) if selected else df
        result['reason']=[f'Fits your equipment and experience limits; targets {r.muscle}. '
                          f'{method} score {r.score:.2f}. Content {r["Content-based"]:.2f}, '
                          f'rating evidence {r.Popularity:.2f}, goal/experience rules {r.Knowledge:.2f}, '
                          f'context {r["Context-aware"]:.2f}.'
                          for _,r in result.iterrows()]
        return result.reset_index(drop=True), {'eligible':int(allowed.sum()), 'method':method}


def make_plan(ranked,profile):
    """Transparent demo time allocation; durations include sets/rest/transitions."""
    if ranked.empty: return ranked.copy()
    profile.validate()
    block=min(5 if profile.energy=='Low' else 7,profile.minutes-5)
    count=min(len(ranked),max(0,(profile.minutes-5)//block))
    plan=ranked.head(count).copy()
    plan['duration_minutes']=block
    plan['suggested_format']=plan.category.map(lambda c:'Easy timed practice' if c in ['cardio','stretching'] else 'Technique-focused sets; choose comfortable load')
    return plan
