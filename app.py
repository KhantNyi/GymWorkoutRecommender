"""A focused, three-method workout builder with local exercise demonstrations."""
from dataclasses import asdict
from html import escape
import json
import math
import pandas as pd
import streamlit as st
from engine import ROOT, Profile, Recommender, GOALS, LEVELS, METHODS, make_plan
from exercise_media import load_manifest, image_paths
import storage

st.set_page_config(page_title='Form & Focus · Workout builder',page_icon='🏋️',layout='wide')
st.markdown('''<style>
.stApp {background:#fff;color:#182b49}
.stApp,.stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label,.stApp input,.stApp button,.stApp textarea {font-family:"Segoe UI",Arial,sans-serif!important}
.block-container {max-width:1180px;padding-top:4rem;padding-bottom:3rem}
[data-testid="stSidebar"] {background:#f6f8fc;border-right:1px solid #e5eaf2}
h1,h2,h3 {color:#182b49;letter-spacing:-.035em}
h1 {font-size:2.65rem!important;font-weight:750!important}
h3 {font-size:1.28rem!important}
[data-testid="stMetric"] {padding:12px 16px;background:#f4f7fc;border-radius:12px}
[data-testid="stMetricValue"] {font-size:1.5rem}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px}
.eyebrow {font-size:11px;letter-spacing:.16em;font-weight:750;color:#3268c8;margin-bottom:12px}
.pill {display:inline-block;background:#eef3fc;color:#355580;padding:5px 10px;border-radius:7px;font-size:12px;margin:0 6px 7px 0}
.no-photo {background:#f3f6fa;border:1px dashed #d7e0ec;border-radius:12px;padding:36px 10px;text-align:center;color:#738299;font-size:13px}
.empty {padding:34px;border-radius:14px;background:#f5f8fd;color:#53647b;margin:16px 0}
.eyebrow,.pill,.no-photo,.empty {font-family:"Segoe UI",Arial,sans-serif}
[data-testid="stImage"] img {border-radius:10px;object-fit:contain}
.stButton button,.stDownloadButton button {border-radius:9px}
[data-testid="stRadio"] label[data-baseweb="radio"] {background:#f4f7fc;border:1px solid #e3eaf4;border-radius:9px;padding:8px 12px;margin-right:8px}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {background:#eaf1ff;border-color:#3268c8}
@media(max-width:640px){.block-container{padding:4rem 1.2rem 1.2rem}h1{font-size:2rem!important}}
</style>''',unsafe_allow_html=True)

LEVEL_LABELS={'beginner':'Beginner','intermediate':'Intermediate','expert':'Advanced'}
DESCRIPTIONS={'Hybrid':'A balanced mix of exercise fit, ratings, goal rules and completion history.',
    'Content-based':'Matches your goal and muscle focus to exercise descriptions and your likes.',
    'Context-aware':'Ranks goal and experience fit together with your exercise completion history.'}
PRESETS={'Bodyweight only':[],'Dumbbells + bench':['dumbbell','bench'],
    'Gym essentials':['dumbbell','bench','barbell','pullup bar','cable','machine']}

@st.cache_data
def load_data(): return pd.read_csv(ROOT/'data/processed/exercises.csv').fillna('')

@st.cache_resource
def get_engine(items,history): return Recommender(items,history)

items=load_data(); manifest=load_manifest(); saved=storage.profiles()
EQUIPMENT=sorted(set('|'.join(items.required_equipment).split('|'))-{'unknown','other','bodyweight'})
FIELDS=['user_id','goal','experience','equipment','minutes','muscles','excluded_muscles','location','energy','age','gender','height_cm','weight_kg']

def initialize(values):
    values=dict(values)
    if values.get('goal')=='Beginner': values.update(goal='General Fitness',experience='beginner')
    values['equipment']=[e for e in values['equipment'] if e!='bodyweight' and e in EQUIPMENT]
    values['height_cm']=float(values['height_cm']); values['weight_kg']=float(values['weight_kg'])
    st.session_state['_draft']=values.copy()
    st.session_state['_applied']={**values,'equipment':['bodyweight']+values['equipment']}
    for field in FIELDS: st.session_state['f_'+field]=values[field]
    st.session_state['equipment_preset']='Custom'

def sync_draft():
    draft=st.session_state['_draft'].copy()
    for field in FIELDS:
        if 'f_'+field in st.session_state: draft[field]=st.session_state['f_'+field]
    st.session_state['_draft']=draft
    if 'workout_method' in st.session_state: st.session_state['_method']=st.session_state['workout_method']

def load_profile():
    chosen=st.session_state['profile_picker']
    defaults=asdict(Profile())
    if chosen=='New profile' and defaults['user_id'] in saved:
        suffix=2
        while f'profile-{suffix}' in saved: suffix+=1
        defaults['user_id']=f'profile-{suffix}'
    initialize(saved.get(chosen,defaults))
    st.session_state['_has_plan']=chosen!='New profile'

def apply_preset():
    selected=st.session_state['equipment_preset']
    if selected in PRESETS:
        st.session_state['f_equipment']=[e for e in PRESETS[selected] if e in EQUIPMENT]
        sync_draft()

def custom_equipment():
    st.session_state['equipment_preset']='Custom'; sync_draft()

def build_workout():
    sync_draft(); draft=st.session_state['_draft']
    try:
        candidate=Profile(**{**draft,'user_id':draft['user_id'].strip(),'equipment':['bodyweight']+draft['equipment']})
        candidate.validate(); storage.save_profile(candidate)
        st.session_state['_applied']=asdict(candidate)
        st.session_state['_has_plan']=True
        st.session_state['_draft']['user_id']=candidate.user_id
        st.session_state['f_user_id']=candidate.user_id
        st.session_state['profile_picker']=candidate.user_id
        st.session_state.pop('_build_error',None)
    except ValueError as exc: st.session_state['_build_error']=str(exc)

def go_log(eid):
    st.session_state['page']='Activity'
    st.session_state['_log_exercise']=eid; st.session_state['log_exercise']=eid

if '_draft' not in st.session_state:
    chosen=next(iter(saved),'New profile')
    initialize(saved.get(chosen,asdict(Profile())))
    st.session_state['profile_picker']=chosen; st.session_state['_has_plan']=chosen!='New profile'

with st.sidebar:
    st.markdown('<div class="eyebrow">FORM & FOCUS</div>',unsafe_allow_html=True)
    st.subheader('Make room for movement.')
    st.caption('A workout built around your day.'); st.divider()
    options=['New profile']+list(saved)
    if st.session_state.get('profile_picker') not in options: st.session_state['profile_picker']='New profile'
    st.selectbox('Saved profile',options,key='profile_picker',on_change=load_profile)
    current=Profile(**st.session_state['_applied'])
    st.caption(f'Active profile: {current.user_id}'); st.divider()
    st.markdown('**Three ways to find your workout**')
    st.caption('Content-based · Context-aware · Hybrid')
    st.caption('Change the method in Build workout. Your equipment and time constraints always apply.')
    with st.expander('About this project'):
        st.caption('Educational prototype for adults. Muscle exclusions use the listed primary muscle only. Exercise durations are planning estimates.')
        st.markdown('[Exercise data](https://www.kaggle.com/datasets/niharika41298/gym-exercise-data) · [Photo source](https://github.com/yuhonas/free-exercise-db)')
        st.caption(f'{len(items):,} catalogue exercises · {len(manifest)} with local photo demonstrations. Profiles and feedback stay on this computer.')

st.markdown('<div class="eyebrow">YOUR PERSONAL WORKOUT SPACE</div>',unsafe_allow_html=True)
st.title('A workout that fits your day.')
st.write('Choose what works for you. Understand each exercise. Keep track of how it went.')
page=st.radio('Workspace',['Build workout','Exercise library','Activity'],horizontal=True,key='page',label_visibility='collapsed',on_change=sync_draft)
st.divider()
history=storage.activities(); profile=Profile(**st.session_state['_applied'])
personal=history[history.user_id.eq(profile.user_id)]

def show_exercise(row,key_prefix,duration=None,method=None):
    eid=row['exercise_id']; photos=image_paths(eid,manifest)
    with st.container(border=True):
        photo_col,detail=st.columns([1,3])
        with photo_col:
            if photos:
                st.image(photos[0],use_container_width=True); st.caption('Photo: Free Exercise DB')
            else: st.markdown('<div class="no-photo">Demonstration image<br>not available yet</div>',unsafe_allow_html=True)
        with detail:
            st.subheader(row['name'])
            tags=[row['muscle'].title(),LEVEL_LABELS.get(row['level'],row['level'].title()),row['required_equipment'].replace('|',', ')]
            if duration is not None: tags.insert(0,f'{int(duration)} min')
            st.markdown(''.join(f'<span class="pill">{escape(t)}</span>' for t in tags),unsafe_allow_html=True)
            description=str(row.get('description','')).strip()
            if description and description!='unknown': st.write(description if len(description)<=260 else description[:257].rsplit(' ',1)[0]+'…')
            else: st.caption('No short description is available for this exercise.')
            with st.expander('How to perform'):
                if photos:
                    st.image(photos,caption=[f'Position {i+1}' for i in range(len(photos))],width=220)
                    st.markdown('[Demonstration source: Free Exercise DB](https://github.com/yuhonas/free-exercise-db)')
                instructions=str(row.get('instructions','')).strip()
                if instructions:
                    for i,line in enumerate(instructions.splitlines(),1): st.write(f'{i}. {line}')
                    st.caption(str(row.get('instruction_source','')))
                elif description and description!='unknown': st.write(description)
                else: st.write('Detailed instructions are not available yet.')
                if duration is not None: st.caption('Allocated time includes practice, rest and transitions; choose a comfortable load.')
            if 'reason' in row:
                with st.expander('Why this exercise?'):
                    st.write(f"Fits your equipment and experience limits; targets {row['muscle']}.")
                    if method is not None:
                        st.write(f"{method} score: {row['score']:.2f}")
                    st.caption('All methods respect your equipment, experience and primary-muscle preferences. Selection also encourages muscle variety.')
            st.button('Log this exercise',key=f'{key_prefix}_{eid}',on_click=go_log,args=(eid,))

if page=='Build workout':
    st.subheader('1. Set up your session')
    for field in FIELDS:
        if 'f_'+field not in st.session_state: st.session_state['f_'+field]=st.session_state['_draft'][field]
    a,b,c=st.columns(3)
    with a: st.selectbox('Training goal',GOALS,key='f_goal',on_change=sync_draft)
    with b: st.selectbox('Experience',list(LEVELS),format_func=LEVEL_LABELS.get,key='f_experience',on_change=sync_draft)
    with c: st.slider('Available time (minutes)',10,180,step=5,key='f_minutes',on_change=sync_draft)
    a,b=st.columns([1,2])
    with a: st.selectbox('Equipment preset',['Custom']+list(PRESETS),key='equipment_preset',on_change=apply_preset)
    with b: st.multiselect('Available equipment',EQUIPMENT,key='f_equipment',on_change=custom_equipment)
    st.caption('Bodyweight exercises are always included. Edit equipment to match what you actually have, including accessories.')
    with st.expander('More preferences'):
        a,b=st.columns(2)
        with a:
            st.multiselect('Focus muscles',sorted(items.muscle.unique()),key='f_muscles',on_change=sync_draft,help='Leave empty for a full-body selection.')
            st.selectbox('Location',['Gym','Home','Outdoors'],key='f_location',on_change=sync_draft)
        with b:
            st.multiselect('Exclude primary muscles',sorted(items.muscle.unique()),key='f_excluded_muscles',on_change=sync_draft)
            st.selectbox('Energy today',['Low','Normal','High'],key='f_energy',on_change=sync_draft)
        st.caption('Low energy limits exercises to beginner difficulty. Outdoors excludes fixed machines and cables.')
    with st.expander('Profile details'):
        st.text_input('Profile alias',max_chars=80,key='f_user_id',on_change=sync_draft)
        st.caption('Your alias links your profile and feedback. The remaining details are optional to edit and do not determine workout ranking.')
        a,b,c,d=st.columns(4)
        with a: st.number_input('Age',18,100,key='f_age',on_change=sync_draft)
        with b: st.number_input('Height (cm)',100.,250.,key='f_height_cm',on_change=sync_draft)
        with c: st.number_input('Weight (kg)',30.,300.,key='f_weight_kg',on_change=sync_draft)
        with d: st.selectbox('Gender',['Prefer not to say','Female','Male','Other'],key='f_gender',on_change=sync_draft)
    draft={**st.session_state['_draft'],'equipment':['bodyweight']+st.session_state['_draft']['equipment']}
    if draft!=st.session_state['_applied']: st.info('You have unapplied changes. Build your workout to use these settings.')
    st.button('Build my workout',type='primary',use_container_width=True,on_click=build_workout)
    if '_build_error' in st.session_state: st.error(st.session_state['_build_error'])
    st.subheader('2. Choose your recommendation method')
    if st.session_state.get('workout_method') not in METHODS: st.session_state['workout_method']=st.session_state.get('_method','Hybrid')
    method=st.radio('Recommendation method',METHODS,horizontal=True,key='workout_method',on_change=sync_draft)
    st.caption(DESCRIPTIONS[method])
    st.caption('Method changes update the built workout immediately. Pending filter edits stay unapplied until you build again.')
    if not st.session_state.get('_has_plan'):
        st.markdown('<div class="empty"><b>Your workout starts here.</b><br>Set your preferences above, then choose Build my workout.</div>',unsafe_allow_html=True)
    else:
        st.divider(); st.subheader('Your workout')
        st.caption(f'Applied settings: {profile.goal} · {LEVEL_LABELS[profile.experience]} · {profile.minutes} min · {profile.location} · {profile.energy.lower()} energy')
        st.caption('Equipment: '+', '.join(profile.equipment)+'. Focus: '+(', '.join(profile.muscles) or 'full body')+'. Exclusions: '+(', '.join(profile.excluded_muscles) or 'none')+'.')
        unseen=st.checkbox('Only exercises I have not logged',key='unseen')
        ranked,meta=get_engine(items,history).recommend(profile,method,top_n=30,exclude_seen=unseen)
        plan=make_plan(ranked,profile)
        if plan.empty: st.info('No exercises match the applied settings. Try adding equipment or clearing muscle restrictions, then build again.')
        else:
            a,b,c=st.columns(3)
            a.metric('Exercises',len(plan)); b.metric('Allocated time',f'{int(plan.duration_minutes.sum())+5} min'); c.metric('Method',method)
            st.caption(f'Includes a 5-minute preparation buffer. {meta["eligible"]} exercises met your constraints.')
            for _,row in plan.iterrows(): show_exercise(row,'plan',row.duration_minutes,method=method)
            a,b=st.columns(2)
            with a: st.download_button('Download workout CSV',plan.to_csv(index=False).encode('utf-8'),'my_workout.csv','text/csv',use_container_width=True)
            with b: st.download_button('Download profile JSON',json.dumps(asdict(profile),indent=2),'profile.json','application/json',use_container_width=True)

elif page=='Exercise library':
    st.subheader('Get to know the movements'); st.write('Browse exercise details before adding them to your routine.')
    a,b,c=st.columns([2,1,1])
    with a: search=st.text_input('Search exercises',placeholder='Try pushups, squat or bear crawl')
    with b: muscle=st.selectbox('Muscle group',['All muscles']+sorted(items.muscle.unique()))
    with c: level=st.selectbox('Difficulty',['All levels']+list(LEVELS),format_func=lambda x:LEVEL_LABELS.get(x,x))
    photos_only=st.checkbox('With demonstration photos only')
    filtered=items[items.name.str.contains(search,case=False,regex=False)].copy()
    if muscle!='All muscles': filtered=filtered[filtered.muscle.eq(muscle)]
    if level!='All levels': filtered=filtered[filtered.level.eq(level)]
    if photos_only: filtered=filtered[filtered.exercise_id.isin(manifest)]
    filtered=filtered.assign(_photo=filtered.exercise_id.isin(manifest)).sort_values(['_photo','name'],ascending=[False,True])
    signature=(search,muscle,level,photos_only)
    if st.session_state.get('_library_filter')!=signature:
        st.session_state['_library_filter']=signature; st.session_state['library_page']=1
    page_count=max(1,math.ceil(len(filtered)/6))
    st.caption(f'{len(filtered):,} {"match" if len(filtered)==1 else "matches"} · Photos cover selected common exercises. Library browsing does not apply your workout constraints.')
    if filtered.empty: st.info('No matching exercises. Try a broader search or clear a filter.')
    else:
        page_number=st.number_input('Results page',1,page_count,key='library_page') if page_count>1 else 1
        for _,row in filtered.iloc[(page_number-1)*6:page_number*6].iterrows(): show_exercise(row,'library')

else:
    st.subheader('Every session is useful feedback')
    st.caption(f'Logging for {profile.user_id}. Each entry records one exercise. Ratings shape preferences; completion informs contextual ranking.')
    if st.session_state.get('log_exercise') not in set(items.exercise_id): st.session_state['log_exercise']=st.session_state.get('_log_exercise',items.exercise_id.iloc[0])
    names=items.set_index('exercise_id')['name'].to_dict()
    with st.form('log',clear_on_submit=False):
        exid=st.selectbox('Exercise completed',items.exercise_id.tolist(),format_func=names.get,key='log_exercise')
        a,b,c=st.columns(3)
        with a: duration=st.number_input('Actual duration (minutes)',1.,480.,7.,key='log_duration')
        with b: completion=st.slider('Completion (%)',0,100,100,key='log_completion')
        with c: rating=st.slider('How much did you like it?',1,5,4,key='log_rating')
        logged=st.form_submit_button('Save activity',type='primary')
    if logged:
        storage.save_profile(profile); storage.log_activity(profile.user_id,exid,duration,completion/100,rating)
        st.session_state['_log_exercise']=exid
        st.success('Activity saved. Your next workout can use this feedback.')
        history=storage.activities(); personal=history[history.user_id.eq(profile.user_id)]
    if personal.empty: st.info('Your first logged exercise will appear here.')
    else:
        a,b,c=st.columns(3)
        a.metric('Logged exercises',len(personal)); b.metric('Total time',f'{personal.duration.sum():g} min'); c.metric('Average completion',f'{personal.completion.mean():.0%}')
        view=personal.merge(items[['exercise_id','name']],on='exercise_id',how='left')
        st.dataframe(view[['created_at','name','duration','completion','rating']].rename(columns={'created_at':'Date (UTC)','name':'Exercise','duration':'Minutes','completion':'Completion','rating':'Rating'}),hide_index=True,use_container_width=True)
        daily=view.assign(day=pd.to_datetime(view.created_at).dt.date).groupby('day').duration.sum()
        st.bar_chart(daily,color='#3268c8')
        st.download_button('Download activity history',view.to_csv(index=False).encode('utf-8'),'activity_history.csv','text/csv')
