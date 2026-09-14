from dataclasses import replace
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import Profile,Recommender,METHODS,LEVELS,GOALS,ROOT,make_plan
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
    assert METHODS==['Hybrid','Content-based','Context-aware']
    for method in METHODS:
        rec,info=engine.recommend(Profile(),method)
        assert len(rec)>0 and np.isfinite(rec.score).all()
        assert info['method']==method
    for method in ['SVD','User CF','Item CF','Popularity','Knowledge']:
        with pytest.raises(ValueError): engine.recommend(Profile(),method)

def test_real_feedback_algorithms_and_unseen(engine):
    ids=engine.items[engine.items.level.eq('beginner')].exercise_id.head(8).tolist()
    history=pd.DataFrame([('a',ids[0],5,1),('a',ids[1],2,.5),('b',ids[0],5,1),
                         ('b',ids[2],4,1),('b',ids[1],2,.5),('c',ids[3],3,.8)],
                         columns=['user_id','exercise_id','rating','completion'])
    model=Recommender(engine.items,history)
    rec,_=model.recommend(Profile(user_id='a'),top_n=100)
    assert np.allclose(rec.score,.4*rec['Content-based']+.2*rec.Popularity+.25*rec.Knowledge+.15*rec['Context-aware'])
    plain,_=engine.recommend(Profile(user_id='a'),top_n=100)
    assert not rec[['exercise_id','score']].equals(plain[['exercise_id','score']])
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

def test_general_fitness_does_not_cap_experience(engine):
    assert 'Beginner' not in GOALS and 'General Fitness' in GOALS
    p=Profile(experience='expert',equipment=sorted(set('|'.join(engine.items.required_equipment).split('|'))))
    ranked,meta=engine.recommend(p,top_n=100)
    assert ranked.level.ne('beginner').any()
    low,_=engine.recommend(replace(p,energy='Low'),top_n=100)
    assert low.level.eq('beginner').all()

def test_legacy_profile_migration_preserves_history(tmp_path):
    import json,sqlite3
    path=tmp_path/'legacy.sqlite3'
    storage.save_profile(Profile(),path)
    storage.log_activity('local-user','ex_pushups',7,1,4,path)
    with sqlite3.connect(path) as con:
        old=json.loads(con.execute('SELECT profile_json FROM profiles').fetchone()[0])
        old.update(goal='Beginner',experience='expert')
        con.execute('UPDATE profiles SET profile_json=?',(json.dumps(old),))
    assert storage.profiles(path)['local-user']['goal']=='General Fitness'
    assert storage.profiles(path)['local-user']['experience']=='beginner'
    assert len(storage.activities(path))==1
    with sqlite3.connect(path) as con:
        records=con.execute('SELECT original_json FROM profile_migrations').fetchall()
        assert len(records)==1 and json.loads(records[0][0])==old

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
    assert app.radio(key='workout_method').options==METHODS
    next(button for button in app.button if button.label=='Build my workout').click().run()
    assert not app.exception
    for method in METHODS:
        app.radio(key='workout_method').set_value(method).run()
        assert not app.exception
        assert next(m for m in app.metric if m.label=='Method').value==method
    assert storage.profiles()['local-user']['goal']=='General Fitness'
    assert storage.activities().empty
    # Changing filters must not silently change the applied profile or saved history.
    app.selectbox(key='f_goal').set_value('Strength').run()
    assert any('unapplied changes' in i.value for i in app.info)
    assert storage.profiles()['local-user']['goal']=='General Fitness'
    app.radio(key='workout_method').set_value('Content-based').run()
    assert any('Applied settings: General Fitness' in c.value for c in app.caption)
    app.radio(key='page').set_value('Exercise library').run()
    assert not app.exception
    app.radio(key='page').set_value('Build workout').run()
    assert app.selectbox(key='f_goal').value=='Strength'
    assert app.radio(key='workout_method').value=='Content-based'
    next(button for button in app.button if button.label=='Build my workout').click().run()
    assert storage.profiles()['local-user']['goal']=='Strength'
    log_button=next(button for button in app.button if button.label=='Log this exercise')
    expected=log_button.key.removeprefix('plan_')
    log_button.click().run()
    assert app.radio(key='page').value=='Activity'
    assert app.selectbox(key='log_exercise').value==expected
    next(button for button in app.button if button.label=='Save activity').click().run()
    assert not app.exception
    assert len(storage.activities())==1
    app.radio(key='page').set_value('Build workout').run()
    assert len(storage.activities())==1
