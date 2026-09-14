# Gym Workout Recommender presentation

- `Gym_Workout_Recommender.pptx`: 16 editable widescreen slides.
- `Gym_Workout_Recommender.pdf`: matching vector PDF.
- `slide_overview.jpg`: overview of all slides.
- `build_presentation.py`: reproducible layout and content source.

Clean white presentation with blue accents, navy typography, pale panels and generous spacing. The 16 slides map the current Streamlit implementation to Chapters 4, 7, 8 and 10, with internal rating and knowledge components acknowledged. It explicitly distinguishes the lecture examples from project-specific representations, context rules, weights and feedback behavior. The app has exactly three methods. General Fitness is a goal; Beginner is experience only. The fixed hybrid contains rating-prior and knowledge components but no collaborative blend. All worked calculations are illustrative. Lecture sources are identified by chapter and code-cell ranges in speaker notes. The deck describes only the Streamlit application.

Validation: the app suite has 28 passing tests, with desktop/mobile browser checks and local image loading verified. The 36 catalogue scenarios were rerun successfully.

The PowerPoint uses native editable text and shapes. The PDF and previews are exported from the same layout source. Run `.venv/Scripts/python.exe presentation/build_presentation.py` from the project root to rebuild (requires python-pptx, reportlab, pymupdf and Pillow).
