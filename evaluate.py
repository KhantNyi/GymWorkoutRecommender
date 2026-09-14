"""Real-catalogue feasibility and optional chronological genuine-feedback evaluation."""
import json
import math
from dataclasses import replace
import pandas as pd
from engine import ROOT,Profile,Recommender,METHODS,GOALS,make_plan,LEVELS
from storage import activities

def main():
    engine=Recommender()
    scenarios=[]
    covered=set()
    for goal in GOALS:
        for location in ['Gym','Home','Outdoors']:
            for minutes in [10,30,60]:
                p=Profile(goal=goal,location=location,minutes=minutes)
                rec,meta=engine.recommend(p,top_n=20)
                plan=make_plan(rec,p)
                ids=set(plan.exercise_id);covered.update(ids)
                allocated=0 if plan.empty else int(plan.duration_minutes.sum())+5
                equip=set(p.equipment)|{'bodyweight'}
                violations=sum(not set(r.required_equipment.split('|'))<=equip for _,r in plan.iterrows())
                scenarios.append(dict(goal=goal,location=location,budget=minutes,eligible=meta['eligible'],
                    planned=len(plan),allocated_minutes=allocated,equipment_violations=violations,
                    budget_violation=allocated>minutes,unique_muscles=int(plan.muscle.nunique())))
    pd.DataFrame(scenarios).to_csv(ROOT/'reports/scenarios.csv',index=False)
    hist=activities()
    metrics=[]
    # Hold out each user's last positive item only if it was never previously observed.
    # Global training excludes all events at or after that timestamp.
    for uid,group in hist.groupby('user_id'):
        positives=group[group.rating>=4]
        if len(positives)<3: continue
        held=positives.iloc[-1]
        train=hist[hist.created_at<held.created_at]
        if held.exercise_id in set(train[train.user_id.eq(uid)].exercise_id): continue
        if held.exercise_id not in engine.lookup: continue
        # Broad profile avoids post-event saved profile leakage. This measures ranking only.
        p=Profile(user_id=uid,goal='Muscle Gain',experience='expert',minutes=60,
                  equipment=sorted(set('|'.join(engine.items.required_equipment).split('|'))))
        model=Recommender(engine.items,train)
        for method in METHODS:
            rec,info=model.recommend(p,method,top_n=10,exclude_seen=True)
            ranked=rec.exercise_id.tolist()
            rank=ranked.index(held.exercise_id)+1 if held.exercise_id in ranked else None
            metrics.append(dict(user_id=uid,method=method,hit=int(rank is not None),
                                ndcg=1/math.log2(rank+1) if rank else 0))
    ranking={'status':'unavailable: no eligible genuine held-out histories; no synthetic accuracy is reported'}
    if metrics:
        scores=pd.DataFrame(metrics)
        scores.to_csv(ROOT/'reports/heldout_users.csv',index=False)
        ranking={'status':'chronological leave-last-positive-out; one relevant item per user; broad profile',
                 'methods':scores.groupby('method').agg(users=('user_id','count'),recall_at_10=('hit','mean'),
                   hit_rate_at_10=('hit','mean'),ndcg_at_10=('ndcg','mean')).reset_index().to_dict('records')}
    report={'catalogue_items':len(engine.items),'scenarios':len(scenarios),
            'budget_violations':sum(s['budget_violation'] for s in scenarios),
            'equipment_violations':sum(s['equipment_violations'] for s in scenarios),
            'scenario_catalogue_coverage':len(covered)/len(engine.items),
            'ranking_evaluation':ranking,
            'limitations':'Scenario coverage describes only tested profiles. No evidence of fitness outcomes or real-world ranking accuracy without adequate genuine feedback.'}
    (ROOT/'reports/evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
