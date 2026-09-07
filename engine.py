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
GOALS=['Beginner','Weight Loss','Muscle Gain','Strength']
METHODS=['Hybrid','Popularity','Content cosine','SVD','User CF','Item CF','Knowledge','Context']
GOAL_TEXT={'Beginner':'beginner strength bodyweight compound',
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
    goal: str='Beginner'
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

    def collaborative(self,user_id):
        """Observed overlap for CF; centered truncated SVD only when feedback exists.

        Missing centered entries are zero residuals, not zero-star observations.
        This is an educational imputation baseline, not observed-only optimization.
        """
        n=len(self.items)
        zero=np.zeros(n)
        hist=self.history[self.history.exercise_id.isin(self.ids)]
        if hist.empty: return {'SVD':zero,'User CF':zero,'Item CF':zero},False
        matrix=hist.pivot_table(index='user_id',columns='exercise_id',values='rating',aggfunc='mean').reindex(columns=self.ids)
        if user_id not in matrix.index or len(matrix)<2: return {'SVD':zero,'User CF':zero,'Item CF':zero},False
        a=matrix.to_numpy(dtype=float); observed=np.isfinite(a)
        means=np.nanmean(a,axis=1); centered=np.where(observed,a-means[:,None],0)
        uidx=matrix.index.get_loc(user_id)
        if observed[uidx].sum()<2: return {'SVD':zero,'User CF':zero,'Item CF':zero},False
        # Cosine on observed ratings; overlap shrinkage prevents one shared rating dominating.
        filled=np.nan_to_num(a)
        usim=cosine_similarity(filled[uidx:uidx+1],filled)[0]
        overlaps=observed.astype(float)@observed[uidx].astype(float)
        usim*=overlaps/(overlaps+3); usim[uidx]=0
        denom=usim@observed
        user_pred=np.divide(usim@filled,denom,out=np.zeros(n),where=denom>0)/5
        # Compute only columns the user rated, avoiding an N x N item matrix.
        rated=np.flatnonzero(observed[uidx])
        isim=cosine_similarity(filled.T,filled[:,rated].T)
        overlap=observed.T.astype(float)@observed[:,rated].astype(float)
        isim*=overlap/(overlap+3)
        for col,idx in enumerate(rated): isim[idx,col]=0
        item_pred=np.divide(isim@a[uidx,rated],isim.sum(axis=1),out=np.zeros(n),where=isim.sum(axis=1)>0)/5
        u,s,vt=np.linalg.svd(centered,full_matrices=False)
        k=min(8,max(1,len(s)-1))
        svd=np.clip(means[uidx]+(u[uidx,:k]*s[:k])@vt[:k],1,5)/5
        svd[~observed.any(axis=0)]=0
        return {'SVD':svd,'User CF':user_pred,'Item CF':item_pred},True

    def recommend(self,profile,method='Hybrid',top_n=8,exclude_seen=False):
        profile.validate()
        if method not in METHODS: raise ValueError('Unknown recommendation method.')
        if not isinstance(top_n,int) or not 1<=top_n<=100: raise ValueError('top_n must be 1–100.')
        df=self.items.copy()
        equipment=set(profile.equipment)|{'bodyweight'}
        if profile.location=='Outdoors': equipment-= {'machine','cable','smith machine'}
        limit=min(LEVELS[profile.experience],0 if profile.goal=='Beginner' or profile.energy=='Low' else 2)
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
                   'Muscle Gain':['strength'],'Beginner':['strength','cardio','stretching']}[profile.goal]
        knowledge=.7*df.category.isin(preferred).to_numpy()+.3*df.level.eq(profile.experience).to_numpy()
        # Local feedback completion supplies a contextual preference signal.
        completion=seen.groupby('exercise_id').completion.mean() if not seen.empty else pd.Series(dtype=float)
        context=.6*knowledge+.4*df.exercise_id.map(completion).fillna(.5).to_numpy()
        cf,ready=self.collaborative(profile.user_id)
        scores={'Popularity':popularity,'Content cosine':content,'Knowledge':knowledge,'Context':context,**cf}
        scores['Hybrid']=.40*content+.20*popularity+.25*knowledge+.15*context
        if ready: scores['Hybrid']=.8*scores['Hybrid']+.2*(cf['SVD']+cf['User CF']+cf['Item CF'])/3
        fallback=method in cf and not ready
        df['score']=scores['Hybrid'] if fallback else scores[method]
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
        result['reason']=[f'{r.muscle}; {r.level}; available equipment; {profile.goal.lower()} match. '
                          f'Content {r["Content cosine"]:.2f}, prior/feedback {r.Popularity:.2f}, rules {r.Knowledge:.2f}.'
                          for _,r in result.iterrows()]
        return result.reset_index(drop=True), {'eligible':int(allowed.sum()),'collaborative_ready':ready,
             'fallback':fallback,'message':'Hybrid fallback: collaborative methods need this user to rate at least 2 exercises and at least 2 users overall.' if fallback else ''}

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

def comparable_sessions(profile,members,k=20):
    """Case-based retrieval from source sessions; never creates exercise-level labels."""
    cols=['Age','Weight (kg)','Height (m)','Experience_Level']
    target=np.array([profile.age,profile.weight_kg,profile.height_cm/100,LEVELS[profile.experience]+1])
    values=members[cols].apply(pd.to_numeric,errors='coerce')
    valid=values.notna().all(axis=1)
    scale=values[valid].std().replace(0,1)
    distance=((values[valid]-target)/scale).pow(2).mean(axis=1).pow(.5)
    cases=members.loc[distance.nsmallest(k).index].copy()
    cases['similarity']=1/(1+distance.loc[cases.index])
    return cases
