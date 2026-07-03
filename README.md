# TruthFit Resume AI

TruthFit Resume AI is a resume and job-fit dashboard for comparing a resume against a job description. It shows fit scores, score drivers, ATS keyword coverage, evidence strength, skill gaps, resume rewrite ideas, project and certification suggestions, chat-based follow-up help, and a lightweight job tracker.

## Screenshots

| Landing | Analyze | Dashboard |
| --- | --- | --- |
| ![Landing](resources/landing.png) | ![Analyze](resources/analyze.png) | ![Dashboard](resources/dashboard.png) |

| Job Details | Skills and ATS | Growth Plan |
| --- | --- | --- |
| ![Job Details](resources/Jobdetails.png) | ![Skills and ATS](resources/skills&ATS.png) | ![Growth Plan](resources/growthplan.png) |

| Chat | Cover Letter | Job Tracker |
| --- | --- | --- |
| ![Chatbot](resources/chatbot.png) | ![Cover Letter](resources/coverletter.png) | ![Job Tracker](resources/JobTracker.png) |

## Features

- Resume upload for PDF, DOCX, and TXT files
- Job description upload or paste input
- Bring-your-own-key provider settings for Gemini, Claude, OpenAI, or Perplexity
- No-API demo dashboard for recruiters and reviewers
- Match scores for overall fit, technical fit, ATS coverage, eligibility, and experience
- Score driver bar explaining what raises or lowers the match score
- Evidence coverage meter for supported, partial, missing, and unsafe claims
- Matched vs missing skills table with importance, resume evidence, and next action
- Top fixes impact/effort matrix for prioritizing resume improvements
- Confidence and evidence check with resume evidence, JD evidence, risk, and manual verification guidance
- Visual dashboard with keyword, requirement, risk, and evidence sections
- Project and certification suggestions tied to missing JD evidence
- Chat helper for analysis questions, cover letters, cold emails, and rewrite help
- Editable job tracker with company, role, link, status, location, salary, and match score
- PDF report export
- Minimal pytest suite and GitHub Actions workflow for CI

## Tech Stack

- Python
- Streamlit
- Google Gemini API
- Anthropic Claude API
- OpenAI API
- Perplexity API
- Plotly
- pandas
- pypdf
- python-docx

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` for local development, or enter a provider API key in the app sidebar:

```env
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

4. Run the app:

```bash
streamlit run app.py
```

## Tests

Install the dev dependency and run the test suite:

```bash
pip install -r requirements-dev.txt
pytest -q
```

The suite covers file loaders, messy LLM JSON extraction, tracker normalization and dedupe behavior, PDF report generation, and UI text cleanup.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Streamlit Cloud and Hugging Face Spaces deployment steps.

## Next Steps

- Add a short recorded demo video below the landing page.
- Add refreshed screenshots after the final dashboard layout is locked.
- Add auth, persistent storage, and server-side usage limits for a production deployment.

## Privacy Note

Resume and job-description text may be sent to the selected provider during live analysis. Do not upload sensitive documents unless you are comfortable sending that content to the provider connected by your API key.

## Git Hygiene

The repo ignores local secrets, virtual environments, logs, tracker data, and generated reports. Do not commit `.env`, `.streamlit/secrets.toml`, real resumes, or private job application data.

## License

Copyright (c) 2026 Sarth.

This project is source-available for portfolio review only. Reuse, redistribution, sublicensing, or commercial use is not permitted without written permission. See [LICENSE](LICENSE).
