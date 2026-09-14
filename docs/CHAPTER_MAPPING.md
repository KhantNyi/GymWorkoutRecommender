# Lecture-to-implementation mapping

Course materials are in the parent Recommender folder. The current app exposes three methods.

| Lecture | Current application |
|---|---|
| Chapters 1–2: foundations and data preparation | Profiles, items, feedback, normalization, ranked recommendations and evaluation. |
| Chapter 3: popularity | Source-rating prior and smoothed local ratings contribute internally to Hybrid. No separate Popularity mode. |
| Chapter 4: content and cosine | Content-based mode uses cosine. The movie example uses CountVectorizer; the app uses TF-IDF exercise attributes and a project-specific 60/40 positive-feedback blend. |
| Chapter 7: knowledge and constraints | Shared equipment, experience and primary-muscle constraints, plus an internal goal/experience score. Case retrieval is not in the simplified app. |
| Chapter 8: context-aware | Context-aware mode combines completion with goal/experience rules. Location and energy constrain all methods; time is allocated afterward. This adapts the concept, not the lecture's preference × time-relevance formula. |
| Chapter 10: weighted hybrid | 40% Content + 20% Popularity + 25% Knowledge + 15% Context. Same generalized weighted-sum mechanism; component definitions and weights are project choices. |

Chapter 10's 5/20-rating switching example is not implemented. SVD and collaborative filtering are not part of the simplified engine. Every selected method uses the same feasibility and muscle-diversity logic. General Fitness is a goal; Beginner is experience only.
