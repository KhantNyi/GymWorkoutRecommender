# Form & Focus — Gym Workout Recommender

A local Streamlit workout builder, visual exercise library and activity tracker. Exactly three methods: **Content-based**, **Context-aware**, **Hybrid**.

## Run

```powershell
python -m pip install -r requirements.txt
./run.ps1
```

Open http://127.0.0.1:8501. The launcher uses the project virtual environment when available. Python 3.11 is recommended.

## Use

1. In **Build workout**, choose General Fitness, Weight Loss, Muscle Gain or Strength. Experience is separate: Beginner, Intermediate or Advanced.
2. Set time and equipment. Presets are editable; bodyweight is always included. Expand **More preferences** for muscles, location and energy.
3. Click **Build my workout** to save and apply settings. Pending edits are marked. Switching methods immediately reranks the applied profile.
4. Inspect descriptions, demonstration photos where available, **How to perform** and **Why this exercise?**
5. Choose **Log this exercise** to preselect it in **Activity**. Record duration, completion and rating. Export your workout, profile or history.

The **Exercise library** has search, muscle/difficulty filters, pagination and a photos-only filter. Library browsing is independent of workout constraints. Demographics are optional to edit and do not affect ranking. Advanced maps to the catalogue's `expert` label.

## Data and logic

- 2,872 unique exercises; 580 instruction matches.
- 24 exercises with locally downloaded demonstrations (48 photos). Missing images are explicitly identified. Exact normalized-name matches prevent related variants receiving incorrect photos.
- Hybrid = `0.40 Content + 0.20 Popularity + 0.25 Knowledge + 0.15 Context`. Popularity and Knowledge are internal components. No collaborative blend or switching rule.
- Profiles and feedback: `data/workouts.sqlite3`. Legacy Beginner goals migrate to General Fitness + Beginner experience; original profiles are preserved in `profile_migrations`, with activities unchanged.
- Member-session data remains archived but is not used by current ranking or UI.

See [design](docs/DESIGN.md), [lecture mapping](docs/CHAPTER_MAPPING.md), [data sources](docs/DATA_SOURCES.md) and [validation](reports/VALIDATION.md). This is an educational prototype with illustrative durations and no validated fitness-outcome claims.

## Reproduce and verify

```powershell
python download_data.py
python prepare_data.py
python prepare_images.py
python -m pytest -q --junitxml=reports/tests.xml
python evaluate.py
```

Prepared data and local photos are included, so runtime needs no image downloads. The image downloader fetches only a bounded selection, validates files, and records URLs and SHA-256 hashes.

Slides and previews: [presentation](presentation/README.md). Install `requirements-presentation.txt` separately to rebuild the deck.
