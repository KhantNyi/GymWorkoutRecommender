# Gym Workout Recommender

Open **[Gym_Workout_Recommender.ipynb](Gym_Workout_Recommender.ipynb)** and select **Run All**. The notebook opens a working interface: enter your profile and equipment, click **Build my workout**, then record completed exercises in **Activity & feedback**. It also includes exercise search and downloadable workouts/history.

All system code is embedded in the notebook. It uses the included `data/processed/` catalogue and saves notebook profiles/feedback separately in `data/notebook_workouts.sqlite3`. It does not require the application Python modules or Streamlit. The code cells are collapsed to keep the interface prominent.

Install notebook dependencies in your selected kernel if needed:

```powershell
python -m pip install -r requirements-notebook.txt
```

Locally, the project `.venv` already contains the notebook dependencies; select `.venv/Scripts/python.exe` as the VS Code notebook kernel. The virtual environment itself is not included in Git.

The standalone notebook replaces the earlier chapter-based teaching notebook. The optional Streamlit application below remains available.

A runnable local application based on the supplied gym workout PPT and chapter materials. It includes goal-based workout plans, saved profiles, equipment/time constraints, exercise search, workout logging, explanations, CSV exports, algorithm comparisons and case-based session retrieval.

## Run

Open PowerShell in this folder:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Open http://localhost:8501. Alternatively, run `./run.ps1` after installing dependencies. The datasets have already been downloaded and prepared; no Kaggle credentials are required to run the app. Python 3.11 is recommended.

1. Enter a user alias, goal, experience, available equipment and current context in the sidebar.
2. Click **Save profile & build workout**.
3. Inspect explanations and export your workout in **Your workout**.
4. Use **Activity & progress** to record actual exercise duration, completion and a rating.
5. Inspect chapter methods and similar downloaded sessions in **Algorithm lab**. Collaborative methods explicitly fall back until the local database has enough feedback.

## Reproduce downloads and checks

```powershell
python download_data.py
python prepare_data.py
python -m pytest -q
python evaluate.py
python run_notebook.py
```

The downloader validates ZIP/JSON contents and reuses existing original files. Checksums and exact source URLs are in `data/source_manifest.json`. Dependencies may require internet on first installation; application use afterward is offline.

Validation on the installed Python 3.11 environment: **30 tests passed**, 36 catalogue scenarios had zero time-budget/equipment violations, and all 7 notebook code cells executed. `requirements-tested.txt` records the exact directly used package versions. One upstream Streamlit/Altair deprecation warning does not affect the checks. See `reports/VALIDATION.md` for scope.

## Project contents

- `app.py`: Streamlit interface, profile editor, catalogue, workout and activity views.
- `engine.py`: popularity, content cosine, SVD, user/item CF, knowledge/context ranking and session allocation.
- `storage.py`: SQLite profile and activity persistence.
- `data/raw/`: two downloaded Kaggle archives/CSVs, exercise JSON, upstream license and metadata.
- `data/processed/`: cleaned exercises and session records.
- `docs/CHAPTER_MAPPING.md`: direct chapter-to-implementation mapping, including the missing chapter 6 file.
- `docs/DESIGN.md`: architecture, formulas, schema, evaluation and limitations.
- `docs/DATA_SOURCES.md`: source links, provenance and dataset boundaries.
- `analysis.ipynb`: coursework walkthrough and reproducible exploration.
- `tests/`: algorithm, constraints, persistence and app smoke tests.
- `reports/`: actual quality, evaluation and validation outputs.

The app is an educational recommender prototype. It does not claim validated training outcomes. Member-session calories are visible as source values; exercise-specific calories are unavailable. No synthetic user histories are inserted. See the design document for scoring assumptions and evaluation limitations.
