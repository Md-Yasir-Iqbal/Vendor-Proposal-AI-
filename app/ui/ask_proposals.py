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
            _clear_messages(user, conversation_id, analysis_id)
            st.session_state.pop(clear_flag, None)
            st.rerun()
        if cancel.button("Cancel", key=f"cancel_clear_button_{analysis_id}", width="stretch"):
            st.session_state.pop(clear_flag, None)
            st.rerun()

    messages = _load_messages(user, conversation_id, analysis_id)
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
    _save_message(conversation_id, f"msg_{uuid4().hex}", "user", question, analysis_id=analysis_id)
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
    _save_message(
        conversation_id, f"msg_{uuid4().hex}", "assistant", answer.answer,
        citations, metadata, analysis_id
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
    list_helper = getattr(chat_database, "list_conversations", None)
    if list_helper is None:
        state_key = f"assistant_temporary_conversation_{analysis_id}"
        return st.session_state.setdefault(state_key, f"temporary_{uuid4().hex}")
    conversations = list_helper(user, analysis_id)
    if conversations:
        return conversations[0]["conversation_id"]
    conversation_id = f"conv_{uuid4().hex}"
    create_helper = getattr(chat_database, "create_conversation", None)
    if create_helper is not None:
        create_helper(user, analysis_id, conversation_id)
    return conversation_id


def _message_key(analysis_id: str) -> str:
    return f"assistant_temporary_messages_{analysis_id}"


def _load_messages(user: str, conversation_id: str, analysis_id: str) -> list[dict]:
    loader = getattr(chat_database, "load_conversation_messages", None)
    if loader is not None:
        return loader(user, conversation_id)
    return st.session_state.get(_message_key(analysis_id), [])


def _save_message(
    conversation_id: str,
    message_id: str,
    role: str,
    content: str,
    citations: list[dict] | None = None,
    tool_metadata: dict | None = None,
    analysis_id: str | None = None,
) -> None:
    saver = getattr(chat_database, "save_conversation_message", None)
    if saver is not None:
        saver(conversation_id, message_id, role, content, citations, tool_metadata)
        return
    # Compatibility only: prevents a stale Streamlit Cloud container from
    # crashing. Normal current deployments use SQLite through the saver above.
    key = _message_key(analysis_id or "unknown")
    st.session_state.setdefault(key, []).append(
        {"message_id": message_id, "role": role, "content": content,
         "citations": citations or [], "tool_metadata": tool_metadata or {}}
    )


def _clear_messages(user: str, conversation_id: str, analysis_id: str) -> None:
    clearer = getattr(chat_database, "clear_conversation", None)
    if clearer is not None:
        clearer(user, conversation_id)
    else:
        st.session_state[_message_key(analysis_id)] = []


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
