# Downloaded sources

| Source | Local files | Role |
|---|---|---|
| [Kaggle Gym Exercise Dataset — niharika41298](https://www.kaggle.com/datasets/niharika41298/gym-exercise-data) | data/raw/gym_exercises.zip, megaGymDataset.csv | 2,918 original exercise descriptions, muscles, equipment, difficulty and source ratings. |
| [Kaggle Gym Members Exercise Dataset — valakhorasani](https://www.kaggle.com/datasets/valakhorasani/gym-members-exercise-dataset) | data/raw/gym_members.zip, gym_members_exercise_tracking.csv | 973 source session records for descriptive analysis and case-based retrieval. |
| [Free Exercise DB — yuhonas](https://github.com/yuhonas/free-exercise-db) | data/raw/exercises.json, FREE_EXERCISE_LICENSE.md | Instruction enrichment by exact normalized name, with original JSON retained. Repository declares public domain / Unlicense; license text included. |

Downloaded through the public Kaggle API and GitHub raw URLs. `data/source_manifest.json` records exact URLs, bytes, verification timestamps and SHA-256 hashes. Kaggle file metadata responses are retained separately; these endpoints return file manifests, **not license declarations**. Consult the linked Kaggle dataset pages for their current terms before redistribution. No account credentials are stored. Raw archives are included as requested for local coursework.

Processing retained 2,872 unique catalogue entries and matched detailed instructions for 580. `reports/data_quality.json` contains actual counts and missingness. Equipment/difficulty/description text is normalized; absent ratings are left missing in the processed file and filled only when constructing the documented ranking prior.

There are no source user–exercise interaction IDs linking these datasets. No member record is assigned an exercise, goal, completion rate or invented history. Local user feedback is a separate SQLite table that starts empty. Member-session calories are presented as source observations only. Downloaded workout types do not establish which individual exercises a member performed.

Roboflow was considered unnecessary because the proposal requires recommendations from profiles and history rather than visual exercise recognition. No unused image-training dataset is downloaded.
