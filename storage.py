"""Local SQLite profiles and genuine feedback; no fabricated training interactions."""
from pathlib import Path
import json
import sqlite3
from datetime import datetime, timezone
import pandas as pd

DB = Path(__file__).resolve().parent/'data/workouts.sqlite3'

def connect(path=DB):
    con=sqlite3.connect(path)
    con.execute('PRAGMA foreign_keys = ON')
    con.executescript('''
    CREATE TABLE IF NOT EXISTS profiles(user_id TEXT PRIMARY KEY, profile_json TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS activities(
      activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL REFERENCES profiles(user_id), exercise_id TEXT NOT NULL,
      duration REAL NOT NULL CHECK(duration>0), completion REAL NOT NULL CHECK(completion BETWEEN 0 AND 1),
      rating REAL NOT NULL CHECK(rating BETWEEN 1 AND 5), created_at TEXT NOT NULL);
    ''')
    return con

def save_profile(profile, path=DB):
    profile.validate()
    from dataclasses import asdict
    with connect(path) as con:
        con.execute('INSERT INTO profiles VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET profile_json=excluded.profile_json',
                    (profile.user_id,json.dumps(asdict(profile))))

def profiles(path=DB):
    with connect(path) as con:
        return {uid:json.loads(data) for uid,data in con.execute('SELECT * FROM profiles ORDER BY user_id')}

def log_activity(user_id, exercise_id, duration, completion, rating, path=DB):
    import math
    if not all(math.isfinite(float(v)) for v in [duration,completion,rating]):
        raise ValueError('Activity values must be finite.')
    if not 0 < duration <= 480 or not 0 <= completion <= 1 or not 1 <= rating <= 5:
        raise ValueError('Invalid duration, completion, or rating.')
    with connect(path) as con:
        con.execute('INSERT INTO activities(user_id,exercise_id,duration,completion,rating,created_at) VALUES(?,?,?,?,?,?)',
                    (user_id,exercise_id,duration,completion,rating,datetime.now(timezone.utc).isoformat()))

def activities(path=DB):
    with connect(path) as con:
        return pd.read_sql_query('SELECT * FROM activities ORDER BY created_at,activity_id',con)
