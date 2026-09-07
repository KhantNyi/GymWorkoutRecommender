"""Run the actual embedded code and widget callbacks against a temporary database."""
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def notebook(tmp_path, monkeypatch):
    import IPython.display
    monkeypatch.setattr(IPython.display, 'display', lambda *args, **kwargs: None)
    monkeypatch.setattr(IPython.display, 'clear_output', lambda *args, **kwargs: None)
    monkeypatch.chdir(ROOT)
    document = json.loads((ROOT/'Gym_Workout_Recommender.ipynb').read_text(encoding='utf-8'))
    scope = {'__name__': '__main__'}
    for cell in document['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source']).replace(
                "DB = ROOT / 'data/notebook_workouts.sqlite3'",
                f'DB = Path({str(tmp_path / "notebook.sqlite3")!r})')
            exec(compile(source, 'notebook', 'exec'), scope)
    return scope

def test_build_save_and_load(notebook):
    n = notebook
    n['user_id'].value = 'test-user'
    n['minutes'].value = 10
    n['build_button'].click()
    assert n['state']['profile'].user_id == 'test-user'
    plan = n['state']['plan']
    assert len(plan) and plan.duration_minutes.sum()+5 <= 10
    assert n['profiles']()['test-user']['minutes'] == 10
    n['minutes'].value = 60
    n['load_button'].click()
    assert n['minutes'].value == 10

def test_feedback_is_saved_once_for_active_profile(notebook):
    n = notebook
    n['build_button'].click()
    active = n['state']['profile'].user_id
    n['user_id'].value = 'unsaved-input'
    n['log_button'].click()
    history = n['activities']()
    assert len(history) == 1
    assert history.iloc[0].user_id == active
    assert history.iloc[0].rating == 4
    assert 'Saved feedback' in n['feedback_status'].value

def test_empty_constraints_and_invalid_profile(notebook):
    n = notebook
    n['focus'].value = ('abdominals',)
    n['exclude'].value = ('abdominals',)
    n['build_button'].click()
    assert n['state']['plan'].empty
    n['user_id'].value = ' '
    n['build_button'].click()
    assert 'user ID' in n['status'].value

def test_library_and_download(notebook):
    n = notebook
    n['search'].value = 'squat'
    n['build_button'].click()
    link = n['download_link']('Download', n['state']['plan'].to_csv(index=False), 'workout.csv')
    assert 'download="workout.csv"' in link and 'base64,' in link
