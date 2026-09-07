| Chapter | Supplied material | Implementation |
|---|---|---|
| 1 — Introduction | RSs Chapter 1.pdf | Profiles, items, feedback, ranked recommendations, explanations, evaluation and export. |
| 2 — Data mining | RSs Chapter 2.pdf | Null handling, title deduplication, normalized categories, TF-IDF, standardized case distance and evaluation. The chapter surveys additional classifiers and clustering; these are not required by this proposal. |
| 3 — Popularity | Popularity notebook | Source rating prior plus Bayesian-smoothed local ratings. Source vote counts are unavailable, so this is explicitly a rating-prior baseline rather than observed global popularity. |
| 4 — Content cosine | Cosine similarity notebook | TF-IDF over exercise content; cosine against goal/focus and the user's liked exercises. |
| 5 — SVD | SVD notebook | Mean-centered user–item feedback, truncated NumPy SVD, reconstructed scores. Missing entries mean zero residual, not zero-star ratings. This imputation baseline retains the limitations explained in the lecture. |
| 6 — Collaborative filtering | **File not supplied.** Topic identified in chapters 7/8 outlines. | User-based and item-based cosine CF with overlap shrinkage, unknown-item handling, and explicit cold-start fallback. |
| 7 — Knowledge based | Knowledge notebook | Hard equipment/level/muscle constraints; goal rules; standardized nearest-case retrieval over downloaded gym sessions. |
| 8 — Context aware | Context notebook | Time budget, location equipment restrictions, energy-based level cap and completion-history adjustment. |

The final weighted combination is an integration choice, not a claim that a chapter 10 file was supplied. Every selectable method uses the same hard constraints. A muscle-diversity penalty affects selection order, so the displayed base scores need not decrease monotonically.
