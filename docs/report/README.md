# Project Report & Presentation

Generated deliverables for the **AI Dropout Predictor** academic / viva package.

## Files

| File | Description |
|------|-------------|
| `AI_Dropout_Predictor_Report.docx` | ~180-page technical report with code snippets |
| `AI_Dropout_Predictor_Presentation.pptx` | 10-slide PowerPoint deck |
| `generate_deliverables.py` | Regenerator script |

## Regenerate

From repo root:

```powershell
backend\.venv\Scripts\python.exe docs\report\generate_deliverables.py
```

Requires `python-docx` and `python-pptx` (installed in backend venv).

## Report Contents

- 21 chapters: Introduction → Conclusion
- 8 appendices: API, env vars, ML features, frontend, Docker, glossary, troubleshooting, viva Q&A
- Real code listings from `backend/` and `frontend/` (features, predict, SHAP, JWT, LLM, chat, column mapper, router, API client)
- Extended case-study narratives

## Presentation (10 Slides)

1. Title  
2. The Problem  
3. Our Solution  
4. Architecture  
5. ML Pipeline  
6. Key Features  
7. Code Highlight  
8. Security & Privacy  
9. Live Demo Flow  
10. Future Scope & Q&A  

## Tips

- Open the DOCX in Word → **References → Table of Contents** to auto-generate TOC.
- Export DOCX to PDF for submission.
- Customize title slide with your name / institution before presenting.
