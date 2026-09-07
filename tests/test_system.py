from dataclasses import replace
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import Profile,Recommender,METHODS,LEVELS,ROOT,make_plan,comparable_sessions
import storage

@pytest.fixture(scope='module')
def engine(): return Recommender()

@pytest.mark.parametrize('method',METHODS)
def test_all_methods_respect_constraints(engine,method):
    p=Profile(equipment=['bodyweight'],excluded_muscles=['abdominals'],location='Outdoors')
    rec,meta=engine.recommend(p,method,20)
    assert len(rec)>0
    assert all(set(e.split('|'))<={'bodyweight'} for e in rec.required_equipment)
    assert rec.level.eq('beginner').all()
    assert not rec.muscle.eq('abdominals').any()
    assert np.isfinite(rec.score).all()
    assert rec.exercise_id.is_unique

@pytest.mark.parametrize('minutes',[10,15,30,60,180])
@pytest.mark.parametrize('energy',['Low','Normal','High'])
def test_plan_budget(engine,minutes,energy):
    p=Profile(minutes=minutes,energy=energy)
    rec,_=engine.recommend(p,top_n=30)
    plan=make_plan(rec,p)
    assert len(plan)>0
    assert plan.duration_minutes.sum()+5<=minutes

def test_no_eligible_items(engine):
    p=Profile(muscles=['nonexistent'])
    rec,meta=engine.recommend(p)
    assert rec.empty and meta['eligible']==0
    assert make_plan(rec,p).empty

def test_cold_start(engine):
    base,_=engine.recommend(Profile())
    rec,info=engine.recommend(Profile(),'SVD')
    assert info['fallback']
    assert rec.exercise_id.tolist()==base.exercise_id.tolist()

def test_real_feedback_algorithms_and_unseen(engine):
    ids=engine.items[engine.items.level.eq('beginner')].exercise_id.head(8).tolist()
    history=pd.DataFrame([('a',ids[0],5,1),('a',ids[1],2,.5),('b',ids[0],5,1),
                         ('b',ids[2],4,1),('b',ids[1],2,.5),('c',ids[3],3,.8)],
                         columns=['user_id','exercise_id','rating','completion'])
    model=Recommender(engine.items,history)
    scores,ready=model.collaborative('a')
    assert ready
    for values in scores.values():
        assert np.isfinite(values).all()
        assert ((values>=0)&(values<=1)).all()
    assert scores['User CF'][engine.lookup[ids[2]]]>0
    assert scores['Item CF'][engine.lookup[ids[2]]]>0
    assert scores['SVD'][engine.lookup[ids[7]]]==0
    rec,_=model.recommend(Profile(user_id='a'),exclude_seen=True)
    assert not set(rec.exercise_id)&set(ids[:2])

def test_profile_validation():
    assert Profile().bmi==24.2
    for change in [dict(height_cm=0),dict(weight_kg=float('nan')),dict(user_id=' '),dict(minutes=0),dict(goal='bad')]:
        with pytest.raises(ValueError): replace(Profile(),**change).validate()

def test_persistence_and_validation(tmp_path):
    path=tmp_path/'test.sqlite3'
    p=Profile(user_id='tester')
    storage.save_profile(p,path)
    storage.save_profile(replace(p,goal='Strength'),path)
    assert storage.profiles(path)['tester']['goal']=='Strength'
    storage.log_activity('tester','exercise',7,.8,4,path)
    assert len(storage.activities(path))==1
    for duration,completion,rating in [(-1,.5,3),(5,2,3),(5,.5,6),(float('nan'),.5,3)]:
        with pytest.raises(ValueError): storage.log_activity('tester','exercise',duration,completion,rating,path)
    assert len(storage.activities(path))==1

def test_cases(engine):
    members=pd.read_csv(ROOT/'data/processed/members.csv')
    cases=comparable_sessions(Profile(),members)
    assert len(cases)==20
    assert cases.similarity.between(0,1).all()
    assert cases.similarity.is_monotonic_decreasing

def test_streamlit_load_and_submit(tmp_path,monkeypatch):
    from streamlit.testing.v1 import AppTest
    # Redirect all storage calls so UI tests never populate the user's database.
    for name in ['profiles','activities','save_profile','log_activity']:
        original=getattr(storage,name)
        def wrapper(*args,_original=original,**kwargs):
            kwargs['path']=tmp_path/'app.sqlite3'
            return _original(*args,**kwargs)
        monkeypatch.setattr(storage,name,wrapper)
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    assert not app.exception
    next(button for button in app.button if button.label=='Save profile & build workout').click().run()
    assert not app.exception
    assert storage.profiles()['local-user']['goal']=='Beginner'
    assert storage.activities().empty
    next(button for button in app.button if button.label=='Save activity').click().run()
    assert not app.exception
    assert len(storage.activities())==1
