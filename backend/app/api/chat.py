"""
Chat and AI Conversation API Endpoints
Provides non-streaming and streaming conversation endpoints with SREE's lively personality,
memory persistence, weather integration, daily briefing, and safe automated tool execution.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import re
from datetime import datetime

from ..ai.ollama_client import ollama_client
from ..ai.universal_router import universal_router
from ..ai.prompts import build_prompt_with_context
from ..database.db import db_manager
from ..memory.manager import memory_manager
from ..automation.executor import automation_executor
from ..automation.security_guard import security_guard, SecurityLevel
from ..automation.crystallizer import skill_crystallizer
from ..services.search import web_search_service
from ..services.weather import weather_service
from ..services.briefing import briefing_engine

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt or speech query")
    model: Optional[str] = Field(None, description="Optional override for model name")
    session_id: Optional[str] = Field(default="default", description="Conversation session ID")
    history: Optional[List[ChatMessage]] = Field(default=[], description="Recent conversation turns")
    memory_context: Optional[str] = Field(default="", description="Relevant memory context")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=1.5)

class ChatResponse(BaseModel):
    model: str
    reply: str
    eval_count: Optional[int] = 0
    eval_duration: Optional[int] = 0
    action_taken: Optional[str] = None

async def handle_proactive_actions(user_message: str) -> Optional[str]:
    """
    Evaluates:
      1. Security Guard pending confirmation answers ("yes", "confirm", "cancel")
      2. Skill Crystallizer 0ms fast paths (shortcuts, apps, system queries)
      3. Memory extraction and sensitive action staging
    """
    # 1. Check pending Security Guard Level 2 confirmations
    handled, action, confirm_msg = security_guard.check_pending_confirmation(user_message)
    if handled:
        if action and action.get("type") == "wipe_data":
            db_manager.clear_conversation()
            return "Confirmation verified. All personal conversation records wiped successfully."
        return confirm_msg

    # 2. Check Skill Crystallizer 0ms Fast Paths
    fast_reply = await skill_crystallizer.execute_fast_path(user_message)
    if fast_reply:
        return fast_reply

    clean_msg = user_message.lower().strip()

    # 3. Check for Level 3 Critical Destructive commands
    eval_level = security_guard.evaluate_intent(intent_type="raw_command", details={"command": clean_msg})
    if eval_level == SecurityLevel.CRITICAL:
        return "🛑 Security Guard Alert: That command is classified as Level 3 (Critical / Destructive) and is strictly blocked for system safety."

    # 4. Data Wipe Intent (Level 2 Sensitive Action)
    if eval_level == SecurityLevel.SENSITIVE and re.search(r"\b(?:wipe|erase|delete(?:\s+all)?)\s+(?:all\s+)?(?:my\s+)?(?:data|records|history|memories)\b", clean_msg):
        res = security_guard.stage_pending_action(
            action_type="wipe_data",
            payload={},
            prompt_message="Permanently erase all personal memories, notes, and conversation records from local SQLite?"
        )
        return res["message"]

    # 4. Memory Intent (e.g. "remember that I prefer dark theme")
    mem_intent = memory_manager.extract_memory_intent(user_message)
    if mem_intent:
        db_manager.add_memory(key=mem_intent["key"], value=mem_intent["value"], category=mem_intent["category"])
        return f"Got it! I've committed that to memory: {mem_intent['key']} is {mem_intent['value']}."

    # 5. Create Note Intent (e.g. "note down: meeting at 3pm", "create note ...")
    note_match = re.search(r"\b(?:create\s+note|take\s+a\s+note|note\s+down)\s*[:\-]?\s*(.+)", user_message, re.IGNORECASE)
    if note_match:
        content = note_match.group(1).strip()
        title = content[:30] + ("..." if len(content) > 30 else "")
        db_manager.create_note(title=title, content=content, tags="assistant")
        return f"Noted! Created a new note: \"{title}\"."

    # 6. Reminder Intent (e.g. "remind me to drink water")
    remind_match = re.search(r"\bremind\s+me\s+to\s+(.+)", user_message, re.IGNORECASE)
    if remind_match:
        task_text = remind_match.group(1).strip()
        db_manager.create_reminder(title=task_text, priority="normal")
        return f"Done! I've added a reminder: {task_text}."

    return None

@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Standard non-streaming conversation endpoint with Universal AI Routing and failover.
    """
    action_reply = await handle_proactive_actions(request.message)
    if action_reply:
        db_manager.save_message(session_id=request.session_id, role="user", content=request.message, model="system")
        db_manager.save_message(session_id=request.session_id, role="assistant", content=action_reply, model="system")
        return ChatResponse(model="system-action", reply=action_reply, action_taken="local_command")

    memory_context = memory_manager.get_memory_context_string()
    
    if not request.history:
        db_history = db_manager.get_conversation_history(session_id=request.session_id, limit=8)
        history_dicts = [{"role": h["role"], "content": h["content"]} for h in db_history]
    else:
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]

    # Web search
    search_match = re.search(r"\b(?:search\s+(?:for|the\s+web\s+for)?|look\s+up|google)\s+(.+)", request.message, re.IGNORECASE)
    if search_match:
        search_query = search_match.group(1).strip()
        search_results = await web_search_service.search(search_query, max_results=3)
        if search_results:
            formatted_results = "\n".join([f"- {r['title']}: {r['snippet']} ({r['url']})" for r in search_results])
            memory_context += f"\n[Live Web Search Results for '{search_query}']:\n{formatted_results}\n(Answer concisely with citations)"

    messages = build_prompt_with_context(
        user_message=request.message,
        memory_context=memory_context,
        conversation_history=history_dicts
    )

    try:
        result = await universal_router.chat(
            messages=messages,
            temperature=request.temperature
        )
        reply_content = result["content"]

        db_manager.save_message(session_id=request.session_id, role="user", content=request.message, model=result["model"])
        db_manager.save_message(
            session_id=request.session_id,
            role="assistant",
            content=reply_content,
            model=result["model"],
            tokens=result.get("eval_count", 0)
        )

        return ChatResponse(
            model=result["model"],
            reply=reply_content,
            eval_count=result.get("eval_count", 0),
            eval_duration=result.get("eval_duration", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Universal AI generation failed: {str(e)}")

@router.post("/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Streaming conversation endpoint with Universal AI Routing and model cascading.
    """
    action_reply = await handle_proactive_actions(request.message)
    if action_reply:
        db_manager.save_message(session_id=request.session_id, role="user", content=request.message, model="system")
        db_manager.save_message(session_id=request.session_id, role="assistant", content=action_reply, model="system")
        
        async def single_action_generator():
            yield action_reply
            
        return StreamingResponse(single_action_generator(), media_type="text/plain; charset=utf-8")

    memory_context = memory_manager.get_memory_context_string()

    search_match = re.search(r"\b(?:search\s+(?:for|the\s+web\s+for)?|look\s+up|google)\s+(.+)", request.message, re.IGNORECASE)
    if search_match:
        search_query = search_match.group(1).strip()
        search_results = await web_search_service.search(search_query, max_results=3)
        if search_results:
            formatted_results = "\n".join([f"- {r['title']}: {r['snippet']} ({r['url']})" for r in search_results])
            memory_context += f"\n[Live Web Search Results for '{search_query}']:\n{formatted_results}\n(Answer concisely with citations)"

    if not request.history:
        db_history = db_manager.get_conversation_history(session_id=request.session_id, limit=8)
        history_dicts = [{"role": h["role"], "content": h["content"]} for h in db_history]
    else:
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]

    messages = build_prompt_with_context(
        user_message=request.message,
        memory_context=memory_context,
        conversation_history=history_dicts
    )

    async def token_generator():
        collected_chunks = []
        try:
            async for chunk in universal_router.chat_stream(
                messages=messages,
                temperature=request.temperature
            ):
                collected_chunks.append(chunk)
                yield chunk
                
            full_reply = "".join(collected_chunks)
            if full_reply:
                db_manager.save_message(session_id=request.session_id, role="user", content=request.message)
                db_manager.save_message(session_id=request.session_id, role="assistant", content=full_reply)
        except Exception as e:
            yield f"\n[Stream Error: {str(e)}]"

    return StreamingResponse(
        token_generator(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/history")
async def get_history(session_id: str = "default"):
    history = db_manager.get_conversation_history(session_id=session_id, limit=50)
    return {"history": history}

@router.delete("/history")
async def clear_history(session_id: str = "default"):
    db_manager.clear_conversation(session_id=session_id)
    return {"status": "success", "message": "Conversation history cleared"}
