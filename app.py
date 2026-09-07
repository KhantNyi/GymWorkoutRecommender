from dataclasses import asdict
import json
import pandas as pd
import streamlit as st
from engine import ROOT, Profile, Recommender, GOALS, LEVELS, METHODS, make_plan, comparable_sessions
import storage

st.set_page_config(page_title='Form & Focus | Workout recommender',page_icon='🏋️',layout='wide')
st.markdown('''<style>
.stApp {background:linear-gradient(140deg,#101822,#162b30); color:#eef4f4}
[data-testid="stSidebar"] {background:#101a23}
h1,h2,h3 {letter-spacing:-.03em}
[data-testid="stMetric"] {background:#20343b;padding:18px;border-radius:12px}
.stButton>button[kind="primary"] {background:#bee66d;color:#14201a;border:0}
</style>''',unsafe_allow_html=True)
st.caption('FORM & FOCUS  /  PERSONAL WORKOUT LAB')
st.title('A workout that fits your day.')
st.write('Choose your goal, available equipment and time. Explore why each exercise fits, then record how it went.')

if not (ROOT/'data/processed/exercises.csv').exists():
    st.error('Dataset preparation is required. Run python download_data.py, then python prepare_data.py.')
    st.stop()

@st.cache_data
def load_data():
    catalogue=pd.read_csv(ROOT/'data/processed/exercises.csv')
    strings=catalogue.select_dtypes('object').columns
    catalogue[strings]=catalogue[strings].fillna('')
    return catalogue,pd.read_csv(ROOT/'data/processed/members.csv')

items,members=load_data()
saved=storage.profiles()
with st.sidebar:
    st.header('Your training profile')
    existing=st.selectbox('Load a profile',['New profile']+list(saved))
    defaults=saved.get(existing,asdict(Profile()))
    with st.form('profile'):
        uid=st.text_input('User ID',defaults['user_id'],max_chars=80)
        goal=st.selectbox('Goal',GOALS,index=GOALS.index(defaults['goal']))
        experience=st.selectbox('Experience',list(LEVELS),index=list(LEVELS).index(defaults['experience']))
        age=st.number_input('Age',18,100,int(defaults['age']))
        genders=['Prefer not to say','Female','Male','Other']
        gender=st.selectbox('Gender',genders,index=genders.index(defaults['gender']))
        height=st.number_input('Height (cm)',100.,250.,float(defaults['height_cm']))
        weight=st.number_input('Weight (kg)',30.,300.,float(defaults['weight_kg']))
        equipment_options=sorted(set('|'.join(items.required_equipment).split('|'))-{'unknown','other','bodyweight'})
        equipment=st.multiselect('Available equipment / accessories',equipment_options,
            default=[e for e in defaults['equipment'] if e in equipment_options])
        st.caption('Bodyweight is always included. Check benches, bars and partner availability too.')
        muscles=st.multiselect('Focus muscles (empty = full body)',sorted(items.muscle.unique()),default=defaults['muscles'])
        excluded=st.multiselect('Exclude primary muscle groups',sorted(items.muscle.unique()),default=defaults['excluded_muscles'])
        minutes=st.slider('Time available (minutes)',10,180,int(defaults['minutes']),5)
        location=st.selectbox('Location',['Gym','Home','Outdoors'],index=['Gym','Home','Outdoors'].index(defaults['location']))
        energy=st.select_slider('Energy',options=['Low','Normal','High'],value=defaults['energy'])
        submitted=st.form_submit_button('Save profile & build workout',type='primary')
    st.caption('Educational prototype for adults. Equipment metadata and workout templates need trainer review. Muscle exclusions only check the listed primary muscle; they are not injury screening.')

if submitted:
    profile=Profile(uid.strip(),age,gender,height,weight,goal,experience,['bodyweight']+equipment,muscles,excluded,minutes,location,energy)
    try:
        storage.save_profile(profile)
        st.session_state['active_profile']=asdict(profile)
        st.success('Profile saved.')
    except ValueError as exc: st.error(str(exc))

profile=Profile(**st.session_state.get('active_profile',defaults))
history=storage.activities()

@st.cache_resource
def get_engine(item_data,feedback):
    return Recommender(item_data,feedback)

engine=get_engine(items,history)
personal=history[history.user_id.eq(profile.user_id)]
a,b,c,d=st.columns(4)
a.metric('Training goal',profile.goal)
b.metric('Session budget',f'{profile.minutes} min')
c.metric('Logged exercises',len(personal))
d.metric('Average completion',f'{personal.completion.mean():.0%}' if len(personal) else '—')
st.caption(f'Active profile: {profile.user_id} · {profile.experience.title()} · {profile.location} · BMI {profile.bmi} (descriptive only)')
workout,explore,progress,lab,data=st.tabs(['Your workout','Exercise library','Activity & progress','Algorithm lab','Data & chapters'])

with workout:
    left,right=st.columns([3,1])
    with right:
        method=st.selectbox('Recommendation method',METHODS)
        unseen=st.checkbox('Only exercises I have not logged')
    ranked,meta=engine.recommend(profile,method,top_n=20,exclude_seen=unseen)
    plan=make_plan(ranked,profile)
    with left:
        st.subheader('Your next session')
        st.caption(f'{meta["eligible"]} exercises meet your constraints. Selection balances relevance and muscle variety.')
    if meta['fallback']: st.info(meta['message'])
    if plan.empty:
        st.info('No workout fits these settings. Add available equipment, clear a muscle focus, or increase the time budget, then save your profile.')
    else:
        allocated=int(plan.duration_minutes.sum())+5
        st.write(f'**{len(plan)} exercises · {allocated} allocated minutes**, including a 5-minute preparation buffer. Durations are planning estimates.')
        for index,row in plan.iterrows():
            with st.container(border=True):
                st.subheader(f'{index+1:02d}  {row["name"]}')
                st.write(f'{row.muscle.title()} · {row.level.title()} · {row.duration_minutes} min · {row.required_equipment.replace("|", ", ")}')
                st.caption(row.reason)
                with st.expander('Exercise details'):
                    st.write(row.description)
                    if row.instructions:
                        for n,line in enumerate(row.instructions.splitlines(),1): st.write(f'{n}. {line}')
                        st.caption(row.instruction_source)
                    else: st.caption('Step-by-step instructions are not available for this exercise.')
                    st.write(row.suggested_format)
        st.download_button('Download workout CSV',plan.to_csv(index=False).encode('utf-8'),'my_workout.csv','text/csv')
        st.download_button('Download profile JSON',json.dumps(asdict(profile),indent=2),'profile.json','application/json')

with explore:
    st.subheader('Explore the exercise catalogue')
    search=st.text_input('Search exercises')
    filtered=items[items.name.str.contains(search,case=False,regex=False)]
    st.dataframe(filtered[['name','muscle','equipment','level','category','source_rating']],hide_index=True,use_container_width=True)
    if len(filtered):
        chosen=st.selectbox('Read exercise details',filtered.exercise_id,format_func=lambda i:items.loc[items.exercise_id.eq(i),'name'].iloc[0])
        row=items[items.exercise_id.eq(chosen)].iloc[0]
        st.write(row.description)
        if row.instructions: st.text(row.instructions)

with progress:
    st.subheader('Record your workout feedback')
    st.caption('Each entry is one exercise, not an entire session. Ratings train the recommendation methods; completion adjusts contextual preferences.')
    if profile.user_id not in saved and not submitted: st.info('Save your profile before logging an exercise.')
    def save_activity(active):
        storage.save_profile(active)
        storage.log_activity(active.user_id,st.session_state.log_exercise,st.session_state.log_duration,
                             st.session_state.log_completion/100,st.session_state.log_rating)
        st.session_state['activity_saved']=True
    with st.form('log'):
        exid=st.selectbox('Exercise completed',items.exercise_id,format_func=lambda i:items.loc[items.exercise_id.eq(i),'name'].iloc[0],key='log_exercise')
        duration=st.number_input('Actual duration (minutes)',1.,480.,7.,key='log_duration')
        completion=st.slider('Completion (%)',0,100,100,key='log_completion')
        rating=st.slider('How much did you like it?',1,5,4,key='log_rating')
        st.form_submit_button('Save activity',on_click=save_activity,args=(profile,))
    if st.session_state.pop('activity_saved',False): st.success('Activity saved.')
    if not personal.empty:
        view=personal.merge(items[['exercise_id','name']],on='exercise_id',how='left')
        st.dataframe(view[['created_at','name','duration','completion','rating']],hide_index=True)
        daily=view.assign(day=pd.to_datetime(view.created_at).dt.date).groupby('day').duration.sum()
        st.bar_chart(daily)
        st.download_button('Export activity history',view.to_csv(index=False),'activity_history.csv','text/csv')
    else: st.write('Your first logged exercise will appear here.')

with lab:
    st.subheader('Compare chapter techniques')
    st.write('All methods apply the same equipment, experience, muscle and location constraints. A diversity adjustment changes selection order after scoring.')
    compare=st.selectbox('Inspect a method',METHODS,key='lab_method')
    result,info=engine.recommend(profile,compare,top_n=10)
    if info['message']: st.info(info['message'])
    st.dataframe(result[['name','score','Content cosine','Popularity','Knowledge','Context','SVD','User CF','Item CF']],hide_index=True)
    st.caption('Scores are ranking signals, not probabilities or predicted fitness outcomes. Source ratings have no vote counts; the popularity prior is not a measured usage frequency.')
    st.subheader('Case-based retrieval: similar source sessions')
    cases=comparable_sessions(profile,members)
    st.dataframe(cases[['Age','Weight (kg)','Experience_Level','Workout_Type','Session_Duration (hours)','Calories_Burned','similarity']],hide_index=True)
    st.caption('Cases are retrieved using standardized age, weight, height and experience. Calories are reported source-session values, not estimates for your recommended exercises. Session records have no exercise IDs or user histories, and are never joined into ratings.')

with data:
    quality=json.loads((ROOT/'reports/data_quality.json').read_text())
    st.subheader('Downloaded, traceable data')
    st.json(quality)
    st.markdown('[Kaggle exercise catalogue](https://www.kaggle.com/datasets/niharika41298/gym-exercise-data) · '
                '[Kaggle gym sessions](https://www.kaggle.com/datasets/valakhorasani/gym-members-exercise-dataset) · '
                '[Free Exercise DB](https://github.com/yuhonas/free-exercise-db)')
    st.write('Original downloads, metadata and SHA-256 checksums are retained in data/. The app works offline after installation.')
    st.markdown((ROOT/'docs/CHAPTER_MAPPING.md').read_text(encoding='utf-8'))
