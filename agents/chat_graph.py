"""LangGraph routing workflow orchestrating Router, History Agent, and RAG Chat nodes."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agents.chat_llm_client import generate_chat_response
from agents.chat_prompts import build_system_prompt
from agents.chat_router_node import classify_intent
from agents.graph_state import ChatGraphState
from agents.history_agent_node import run_history_query
from app_logging.logger import get_logger
from config.constants import RELEVANT_SCORE_THRESHOLD
from services.retrieval_service import RetrievalService
from services.safety_context_service import SafetyContextService

logger = get_logger(__name__)


def run_rag_chat(state: ChatGraphState) -> ChatGraphState:
    """Execute RAG retrieval and LLM generation for medical QA intent."""
    patient_id = state.get("patient_id", "")
    question = state.get("question", "")
    history_dicts = state.get("conversation_history", [])

    retrieval_service = RetrievalService()
    safety_service = SafetyContextService()

    retrieved_chunks = retrieval_service.retrieve_relevant_chunks(
        question=question,
        patient_id=patient_id,
        top_k=5,
    )

    top_score = max((c.score for c in retrieved_chunks), default=0.0)
    valid_chunks = [c for c in retrieved_chunks if c.score >= RELEVANT_SCORE_THRESHOLD]
    fallback_taken = len(valid_chunks) == 0

    if fallback_taken:
        logger.info(
            "Chat retrieval fallback path taken: insufficient relevance",
            path="medical_qa",
            patient_id=str(patient_id),
            retrieved_chunk_count=len(retrieved_chunks),
            top_score=top_score,
            threshold=RELEVANT_SCORE_THRESHOLD,
        )
        context_texts = ["No specific matching medical records were found for this question."]
        citations_list = []
    else:
        context_texts = [c.text for c in valid_chunks]
        citations_list = [
            {
                "document_id": str(c.document_id),
                "chunk_type": str(c.chunk_type),
                "score": float(c.score),
            }
            for c in valid_chunks
        ]

    safety_context = safety_service.get_safety_context(patient_id=patient_id)
    system_prompt = build_system_prompt(
        allergies=safety_context["allergies"],
        chronic_conditions=safety_context["chronic_conditions"],
    )
    answer = generate_chat_response(
        system_prompt=system_prompt,
        conversation_history=history_dicts,
        context_chunks=context_texts,
        question=question.strip(),
    )

    state["answer"] = answer
    state["citations"] = citations_list
    state["retrieved_chunks"] = valid_chunks

    logger.info(
        "RAG chat node executed",
        path="medical_qa",
        patient_id=str(patient_id),
        retrieved_chunk_count=len(retrieved_chunks),
        fallback_taken=fallback_taken,
    )
    return state


def _init_graph():
    graph = StateGraph(ChatGraphState)
    graph.add_node("router", classify_intent)
    graph.add_node("history_agent", run_history_query)
    graph.add_node("rag_chat", run_rag_chat)

    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        lambda state: state.get("intent", "medical_qa"),
        {
            "history_query": "history_agent",
            "medical_qa": "rag_chat",
        },
    )
    graph.add_edge("history_agent", END)
    graph.add_edge("rag_chat", END)

    return graph.compile()


_COMPILED_GRAPH = _init_graph()


def build_chat_graph():
    """Return the singleton compiled LangGraph routing graph."""
    return _COMPILED_GRAPH
