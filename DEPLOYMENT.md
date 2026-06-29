# Deployment Guide

TruthFit Resume AI can be deployed on Streamlit Cloud or Hugging Face Spaces.

## Streamlit Cloud

1. Push this project to GitHub.
2. Go to Streamlit Cloud and create a new app from the repository.
3. Set the main file path to:

```text
app.py
```

4. Add optional secrets in Streamlit Cloud only if you want to provide hosted provider keys:

```toml
GEMINI_API_KEY = ""
ANTHROPIC_API_KEY = ""
OPENAI_API_KEY = ""
PERPLEXITY_API_KEY = ""
```

5. Deploy.

For public portfolio use, the safest setup is to avoid hosted keys and let visitors enter their own API key in the sidebar.

## Hugging Face Spaces

1. Create a new Space.
2. Choose the Streamlit SDK.
3. Upload this repository.
4. Keep `app.py` at the project root.
5. Add secrets in Space settings only if you want hosted provider keys.

## Privacy

Resume and job description text may be sent to the selected AI provider during live analysis. Do not upload sensitive documents unless you are comfortable sending that content to the selected provider.
