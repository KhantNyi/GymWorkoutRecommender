# Validation

- `python -m pytest -q --junitxml=reports/tests.xml`: **30 passed**, one upstream Streamlit/Altair deprecation warning. UI validation uses Streamlit AppTest; no browser screenshot or visual rendering audit was performed.
- UI test loads the app, saves a profile, confirms the database has no activity yet, logs one exercise and verifies exactly one persisted activity. Tests use temporary databases and do not seed the app database.
- Algorithm tests cover all eight selectable methods under equipment/experience/excluded-muscle constraints, cold-start fallback, genuine-feedback code paths using synthetic unit fixtures, exclusion of seen items, finite collaborative scores, unknown-item behavior and empty results.
- Plan tests cover 10, 15, 30, 60 and 180 minutes at low, normal and high energy. The minimum session exposed a short-budget allocation issue, fixed by shortening its exercise block.
- Persistence tests cover profile updates, activity storage and rejection of invalid/nonfinite values.
- `python evaluate.py`: **36 real-catalogue scenarios**, zero equipment violations and zero time-budget violations. Scenario catalogue coverage is approximately 0.63%, reflecting the narrow beginner/default-equipment scenario set; it is not overall recommendation quality.
- `python run_notebook.py`: **7 code cells executed**; outputs saved in `analysis.ipynb`. This runner executes cells in-process and captures text outputs without requiring Jupyter. Standard Jupyter can also open/run the notebook after installing its own environment.
- All six downloaded source/license/metadata files verified against their SHA-256 manifest entries. The two original ZIPs and their CSV contents are retained.

No genuine activity history is available at delivery, so Recall@10 and NDCG@10 are unavailable. No synthetic accuracy or fitness-outcome validation is claimed. The app is local-only and has not undergone a deployment/security audit.
