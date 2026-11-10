"""Simple persistent, read-only assistant interface for proposal questions."""
from __future__ import annotations

from uuid import uuid4

import streamlit as st

from app.ai.proposal_agent import answer_proposal_question
from app.persistence import database as chat_database
from app.utils.state import get_chroma_store, get_groq_client, get_requirements, get_vendor_results


def render_launcher() -> None:
    """Global top-right control. The popover closes with Escape."""
    with st.popover("AI", help="Ask the Proposals", use_container_width=True):
        _render_panel()


def render() -> None:
    """Compatibility entry point; the assistant normally opens from the header."""
    _render_panel()


def _render_panel() -> None:
    st.markdown("### Ask the Proposals")
    st.caption("Your AI assistant for vendor proposal analysis. Read-only, with proposal citations.")
    user = st.session_state.get("auth_user")
    analysis_id = st.session_state.get("project_id")
    results = [result for result in get_vendor_results().values() if not result.extraction_failed]
    if not user or not analysis_id:
        st.info("Open an analysis workspace to start a conversation.")
        return

    # One chat per analysis: no timestamp dropdown or duplicate chat list.
    conversation_id = _get_conversation(user, analysis_id)
    st.caption("Conversation saved with this analysis.")
    clear_flag = f"assistant_clear_requested_{analysis_id}"
    if st.button("Clear conversation", key=f"clear_chat_{analysis_id}", width="stretch"):
        st.session_state[clear_flag] = True
    if st.session_state.get(clear_flag):
        st.warning("Clear this analysis conversation? This cannot affect other analyses.")
        confirm, cancel = st.columns(2)
        if confirm.button("Confirm", type="primary", key=f"confirm_clear_button_{analysis_id}", width="stretch"):
            chat_database.clear_conversation(user, conversation_id)
            st.session_state.pop(clear_flag, None)
            st.rerun()
        if cancel.button("Cancel", key=f"cancel_clear_button_{analysis_id}", width="stretch"):
            st.session_state.pop(clear_flag, None)
            st.rerun()

    messages = chat_database.load_conversation_messages(user, conversation_id)
    _render_messages(messages)
    if not results:
        st.info("Upload and analyze proposals before asking a question.")
        return

    question = st.chat_input(
        "Ask about price, support, risks, requirements, or evidence...",
        key=f"assistant_input_{analysis_id}",
    )
    if question:
        requirements = get_requirements()
        _answer(question, analysis_id, conversation_id, results, messages, requirements.project_name if requirements else None)


def _answer(question: str, analysis_id: str, conversation_id: str, results, messages: list[dict], project_name: str | None) -> None:
    # Capture analysis/conversation IDs before the request. The response is
    # therefore saved against this analysis even if the workspace changes.
    chat_database.save_conversation_message(conversation_id, f"msg_{uuid4().hex}", "user", question)
    context = [{"role": item["role"], "content": item["content"]} for item in messages[-8:]]
    with st.spinner("Selecting tools and retrieving verified proposal evidence..."):
        answer = answer_proposal_question(
            get_groq_client(), question, results, get_chroma_store(analysis_id), context, project_name
        )
    citations = [
        {"id": f"E{index}", "vendor": item.vendor, "document": item.document,
         "page_number": item.page_number, "section": item.section, "source_text": item.source_text}
        for index, item in enumerate(answer.evidence, start=1)
    ]
    metadata = {
        "generated_by": answer.generated_by,
        "tools_used": answer.tools_used,
        "execution_details": answer.execution_details,
    }
    chat_database.save_conversation_message(
        conversation_id, f"msg_{uuid4().hex}", "assistant", answer.answer, citations, metadata
    )
    st.rerun()


def _get_conversation(user: str, analysis_id: str) -> str:
    """Resolve the current analysis chat without brittle symbol imports.

    This also allows a Streamlit Cloud container that is finishing an older
    deployment to load the application instead of failing at module import.
    """
    helper = getattr(chat_database, "get_or_create_analysis_conversation", None)
    if helper is not None:
        return helper(user, analysis_id)
    # Compatibility path for an older database module; it is only relevant
    # during a stale deployment and uses the same SQLite persistence helpers.
    conversations = chat_database.list_conversations(user, analysis_id)
    if conversations:
        return conversations[0]["conversation_id"]
    conversation_id = f"conv_{uuid4().hex}"
    chat_database.create_conversation(user, analysis_id, conversation_id)
    return conversation_id


def _render_messages(messages: list[dict]) -> None:
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] != "assistant":
                continue
            citations = message.get("citations", [])
            if citations:
                with st.expander(f"Cited proposal evidence ({len(citations)})", expanded=False):
                    for item in citations:
                        st.markdown(
                            f"**[{item['id']}] {item['vendor']}** | {item.get('document') or 'document'} | "
                            f"Page {item.get('page_number') or '-'} | {item.get('section') or 'General'}"
                        )
                        st.caption(item["source_text"])
            metadata = message.get("tool_metadata", {})
            if metadata:
                with st.expander("Agent Execution Details", expanded=False):
                    status = "Completed" if metadata.get("generated_by") == "agent" else "Fallback response"
                    st.write(f"**Execution status:** {status}")
                    st.write("**Tools selected and executed:** " + (", ".join(metadata.get("tools_used", [])) or "None"))
                    for event in metadata.get("execution_details", []):
                        st.caption(f"{event.get('tool')}: {event.get('status')} - {event.get('output')}")
