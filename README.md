# TruthFit Resume AI

TruthFit Resume AI is a resume and job-fit dashboard for comparing a resume against a job description. It shows fit scores, ATS keyword coverage, skill gaps, resume rewrite ideas, project and certification suggestions, chat-based follow-up help, and a lightweight job tracker.

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
- Visual dashboard with keyword, requirement, risk, and evidence sections
- Project and certification suggestions tied to missing JD evidence
- Chat helper for analysis questions, cover letters, cold emails, and rewrite help
- Editable job tracker with company, role, link, status, location, salary, and match score
- PDF report export

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

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Streamlit Cloud and Hugging Face Spaces deployment steps.

## Next Steps

- Add a short recorded demo video below the landing page.
- Add automated tests for loaders, provider parsing, tracker logic, and report generation.

## Privacy Note

Resume and job-description text may be sent to the selected provider during live analysis. Do not upload sensitive documents unless you are comfortable sending that content to the provider connected by your API key.

## Git Hygiene

The repo ignores local secrets, virtual environments, logs, tracker data, and generated reports. Do not commit `.env`, `.streamlit/secrets.toml`, real resumes, or private job application data.

## License

Copyright (c) 2026 Sarth.

This project is source-available for portfolio review only. Reuse, redistribution, sublicensing, or commercial use is not permitted without written permission. See [LICENSE](LICENSE).
