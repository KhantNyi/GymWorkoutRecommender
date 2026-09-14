# Gym Workout Recommender design

## Architecture and interaction

Streamlit provides Build workout, Exercise library and Activity pages. CSV data feeds a TF-IDF engine; SQLite supplies profiles and genuine feedback. Images are attached through a verified local manifest.

The editor separates draft and applied profiles. Edits show an unapplied-change notice; Build my workout validates, saves and applies them. Method switching immediately reranks the applied profile. Page navigation preserves draft filters and selected method. Loading a profile replaces draft and applied settings. The applied settings appear above the workout. Library browsing is independent of workout constraints.

## Profiles and persistence

Goals: General Fitness, Weight Loss, Muscle Gain, Strength. Experience: beginner, intermediate, expert (displayed as Advanced). Equipment always includes bodyweight; presets are editable. Primary-muscle focus/exclusions, available minutes, location and energy constrain the plan. Demographics are optional to edit and do not affect ranking.

SQLite stores profile JSON and exercise activities (user, exercise ID, actual duration, completion 0–1, rating 1–5, UTC timestamp). Legacy Beginner goals migrate to General Fitness + beginner experience. Original JSON is preserved once in `profile_migrations`; user IDs and activities remain unchanged. Repeated migration is idempotent.

## Ranking and allocation

Only Content-based, Context-aware and Hybrid can be selected. SVD, user/item CF and case retrieval were removed.

1. Filter by available equipment, experience and primary-muscle preferences. Low energy caps difficulty at beginner independently of goal. Outdoors removes machine/cable/Smith-machine availability. Unknown or other source equipment remains ineligible through the UI.
2. **Content C:** TF-IDF over exercise name, description, category, primary muscle, level and equipment; cosine against a goal/focus query. Ratings ≥4 add a liked-exercise centroid: 60% query + 40% centroid similarity. Without likes, use query similarity alone.
3. **Popularity P (internal):** `(5 × prior + count × mean) / (5 + count)`. Source ratings are divided by 10; missing values use the median. Local ratings are divided by 5. This is rating evidence, not observed usage frequency or exercise quality validation.
4. **Knowledge K (internal):** `0.7 × goal/category match + 0.3 × experience match`. General Fitness matches strength/cardio/stretching; Weight Loss cardio/plyometrics; Muscle Gain strength; Strength strength/powerlifting. Matches are binary.
5. **Context X:** `0.6K + 0.4 × personal mean completion`; unobserved completion defaults to 0.5. Location and energy affect shared feasibility; time is allocated afterward.
6. **Hybrid B:** `0.40C + 0.20P + 0.25K + 0.15X`. Weights stay fixed as project defaults. Feedback changes components, never switches methods. K is reused in X, so components are not independent: the effective rule contribution is 0.34K.
7. Greedy diversity subtracts 0.10 per previously selected exercise sharing its primary muscle. Score columns show base scores, not this adjustment.
8. Reserve five minutes for preparation. Allocate five-minute blocks for low energy, seven otherwise, shortening for the minimum ten-minute session when necessary. Selected exercises cannot exceed the budget. Durations include practice/rest/transitions and are illustrative.

## Demonstrations

`data/images/manifest.json` maps 24 exact catalogue matches to 48 local photos, with source URLs and SHA-256 hashes. The Free Exercise DB license is retained. Missing media and instructions have explicit fallback states. Plain Bear crawl does not inherit a sled-drag image. Photo availability only affects library display order, never recommendation ranking or feasibility.

## Evaluation limits

Tests cover constraints, fixed hybrid math, duration, rejected retired methods, migration, persistence, UI state and image integrity. `evaluate.py` runs 36 catalogue scenarios and conditionally evaluates chronological genuine held-out positives. Missing ranking accuracy is reported as unavailable. Source sessions are not joined into exercise ratings. Exercise-specific calories are unavailable. No fitness-outcome validation, authentication or deployment hardening is claimed; the server binds to localhost.
