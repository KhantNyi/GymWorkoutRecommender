# Validation — simplified Streamlit app

- `python -m pytest -q --junitxml=reports/tests.xml`: **28 passed**, one upstream Streamlit/Altair deprecation warning. Tests use temporary databases and do not seed the user database.
- All three methods are checked for equipment, experience and excluded-muscle constraints. Removed methods are rejected. Feedback tests verify the fixed Hybrid formula remains unchanged by the presence of multiple users. General Fitness does not force beginner experience.
- Time allocation is checked at 10, 15, 30, 60 and 180 minutes at low, normal and high energy.
- Migration tests verify Beginner goal → General Fitness + beginner experience, preservation of the original profile and activity history, and idempotence. Persistence rejects invalid/nonfinite values.
- UI tests verify three method choices, building/saving a profile, changing methods, draft-filter warnings, applied-profile stability, draft and method persistence across page navigation, prefilled exercise logging, and no duplicate logging on navigation.
- Media tests verify 24 exact source/catalogue matches, all 48 local image hashes and decodability, missing-file fallback and path containment. Plain Bear crawl is explicitly checked to have no misleading variant photo.
- `python evaluate.py`: **36 real-catalogue scenarios**, zero equipment violations and zero time-budget violations. Coverage is approximately **0.45%** for this narrow beginner/default-equipment scenario set; it is not overall ranking quality.
- Headless Edge/Playwright checks cover desktop (1440px) and mobile (390px), navigation, method selection, library search and loading local images. No horizontal overflow was detected. Screenshots: `ui_builder.png`, `ui_library.png`, `ui_mobile.png`. The optional `check_browser.py` requires Playwright and a locally installed Edge browser.

Recall@10 and NDCG@10 remain unavailable without eligible genuine held-out histories. No synthetic accuracy or fitness-outcome validation is claimed. The app binds to localhost and has not undergone a deployment/security audit.
