import streamlit as st

from source.ai.chat_client import generate_analysis_chat_response
import source.ui.components as ui


def show_chat_page():
    ui.render_page_header(
        "Analysis Chat",
        "Ask follow-up questions, generate cover letters, and draft recruiter outreach from your current analysis.",
    )

    if not st.session_state.analysis_result:
        st.warning("No analysis found. Go to Analyze first, then come back to chat.")

        if st.button("Go to Analyze", type="primary"):
            st.session_state.page = "Analyze"
            st.rerun()

        return

    quick_prompts = {
        "Explain Score": "Explain my score and the top three things I should fix first.",
        "Cover Letter": "Create a concise cover letter for this role based only on my evidence.",
        "Cold Email": "Write a short cold email to a recruiter or hiring manager for this role.",
        "Project Ideas": "Suggest the best portfolio projects I should build for this job.",
    }

    prompt_cols = st.columns(4, gap="small")

    for column, (label, prompt) in zip(prompt_cols, quick_prompts.items()):
        with column:
            if st.button(label, width="stretch"):
                st.session_state.pending_chat_prompt = prompt

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Ask about this analysis, cover letter, cold email, or project plan...")

    if st.session_state.get("pending_chat_prompt"):
        user_prompt = st.session_state.pop("pending_chat_prompt")

    if not user_prompt:
        return

    st.session_state.chat_messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking through your analysis..."):
            try:
                response = generate_analysis_chat_response(
                    question=user_prompt,
                    analysis_result=st.session_state.analysis_result,
                    resume_text=st.session_state.resume_text,
                    job_description=st.session_state.jd_text,
                    provider=st.session_state.provider,
                    model=st.session_state.model,
                    api_key=st.session_state.api_key,
                )
            except Exception as exc:
                response = f"Chat failed: {str(exc)}"

            st.markdown(response)

    st.session_state.chat_messages.append({"role": "assistant", "content": response})
