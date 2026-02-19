import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.db import database
from core.dependencies import get_current_user_http
from services.gmail_watch import start_watch, stop_watch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auto-reply", tags=["auto-reply"])


# --- Pydantic Models ---

class AutoReplyRuleCreate(BaseModel):
    name: str = Field(max_length=255)
    when_condition: str = Field(min_length=1)
    do_action: str = Field(min_length=1)
    tone: str = 'Professional'


class AutoReplyRuleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    when_condition: str | None = Field(default=None, min_length=1)
    do_action: str | None = Field(default=None, min_length=1)
    tone: str | None = None


class ReorderRulesRequest(BaseModel):
    rule_ids: list[str]


# --- Watch Routes ---

@router.get("/watch")
async def get_watch_status(user: Any = Depends(get_current_user_http)):
    state = await database.fetch_one(
        "SELECT is_active FROM public.gmail_watch_state WHERE user_id = %s",
        (user.id,)
    )
    return {"is_active": bool(state and state['is_active'])}


@router.post("/watch/toggle")
async def toggle_watch(user: Any = Depends(get_current_user_http)):
    state = await database.fetch_one(
        "SELECT is_active FROM public.gmail_watch_state WHERE user_id = %s",
        (user.id,)
    )
    try:
        if state and state['is_active']:
            await stop_watch(str(user.id))
            return {"is_active": False}
        else:
            await start_watch(str(user.id))
            return {"is_active": True}
    except Exception as e:
        logger.error(f"Failed to toggle watch: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to toggle watch")


# --- Rule Routes ---

@router.post("/rules")
async def create_rule(
        rule: AutoReplyRuleCreate,
        user: Any = Depends(get_current_user_http)
):
    try:
        row = await database.fetch_one(
            """
            INSERT INTO public.auto_reply_rules
                (user_id, name, when_condition, do_action, tone, sort_order)
            VALUES (%s, %s, %s, %s, %s,
                    COALESCE((SELECT MAX(sort_order) + 1 FROM public.auto_reply_rules WHERE user_id = %s), 1))
            RETURNING id, user_id, name, is_enabled, when_condition, do_action, tone,
                      sort_order, created_at, updated_at
            """,
            (user.id, rule.name, rule.when_condition, rule.do_action, rule.tone, user.id)
        )
        return _format_rule(row)
    except Exception as e:
        logger.error(f"Failed to create rule: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create rule")


@router.get("/rules")
async def list_rules(user: Any = Depends(get_current_user_http)):
    try:
        rows = await database.fetch_all(
            """
            SELECT id, user_id, name, is_enabled, when_condition, do_action, tone,
                   sort_order, created_at, updated_at
            FROM public.auto_reply_rules
            WHERE user_id = %s
            ORDER BY sort_order ASC
            """,
            (user.id,)
        )
        return [_format_rule(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to list rules: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list rules")


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: str, user: Any = Depends(get_current_user_http)):
    row = await database.fetch_one(
        """
        SELECT id, user_id, name, is_enabled, when_condition, do_action, tone,
               sort_order, created_at, updated_at
        FROM public.auto_reply_rules
        WHERE id = %s AND user_id = %s
        """,
        (rule_id, user.id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Rule not found")
    return _format_rule(row)


@router.put("/rules/{rule_id}")
async def update_rule(
        rule_id: str,
        update: AutoReplyRuleUpdate,
        user: Any = Depends(get_current_user_http)
):
    existing = await database.fetch_one(
        "SELECT id FROM public.auto_reply_rules WHERE id = %s AND user_id = %s",
        (rule_id, user.id)
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Rule not found")

    fields = []
    values = []
    update_data = update.model_dump(exclude_unset=True)

    for field_name, value in update_data.items():
        fields.append(f"{field_name} = %s")
        values.append(value)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    fields.append("updated_at = NOW()")
    values.extend([rule_id, user.id])

    try:
        row = await database.fetch_one(
            f"""
            UPDATE public.auto_reply_rules
            SET {', '.join(fields)}
            WHERE id = %s AND user_id = %s
            RETURNING id, user_id, name, is_enabled, when_condition, do_action, tone,
                      sort_order, created_at, updated_at
            """,
            tuple(values)
        )
        return _format_rule(row)
    except Exception as e:
        logger.error(f"Failed to update rule: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update rule")


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str, user: Any = Depends(get_current_user_http)):
    existing = await database.fetch_one(
        "SELECT id FROM public.auto_reply_rules WHERE id = %s AND user_id = %s",
        (rule_id, user.id)
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Rule not found")

    try:
        await database.execute(
            "DELETE FROM public.auto_reply_rules WHERE id = %s AND user_id = %s",
            (rule_id, user.id)
        )
        return {"message": "Rule deleted"}
    except Exception as e:
        logger.error(f"Failed to delete rule: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete rule")


@router.patch("/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: str, user: Any = Depends(get_current_user_http)):
    row = await database.fetch_one(
        """
        UPDATE public.auto_reply_rules
        SET is_enabled = NOT is_enabled, updated_at = NOW()
        WHERE id = %s AND user_id = %s
        RETURNING id, user_id, name, is_enabled, when_condition, do_action, tone,
                  sort_order, created_at, updated_at
        """,
        (rule_id, user.id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Rule not found")
    return _format_rule(row)


@router.post("/rules/reorder")
async def reorder_rules(
        body: ReorderRulesRequest,
        user: Any = Depends(get_current_user_http)
):
    if not body.rule_ids:
        raise HTTPException(status_code=400, detail="rule_ids must not be empty")

    try:
        async with database.transaction() as conn:
            async with conn.cursor() as cur:
                for position, rule_id in enumerate(body.rule_ids, start=1):
                    await cur.execute(
                        "UPDATE public.auto_reply_rules SET sort_order = %s, updated_at = NOW() "
                        "WHERE id = %s AND user_id = %s",
                        (position, rule_id, user.id)
                    )
        return {"message": "Rules reordered"}
    except Exception as e:
        logger.error(f"Failed to reorder rules: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reorder rules")


@router.get("/log")
async def get_auto_reply_log(user: Any = Depends(get_current_user_http)):
    try:
        rows = await database.fetch_all(
            """
            SELECT id, message_id, replied_at, reply_message_id, status, error_message, llm_model, subject
            FROM public.auto_reply_log
            WHERE user_id = %s
            ORDER BY replied_at DESC
            LIMIT 50
            """,
            (user.id,)
        )
        return [_format_log_entry(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch log: {e}", extra={"user_id": user.id}, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch log")


# --- Helpers ---

def _format_rule(row: dict) -> dict:
    return {
        "id": str(row['id']),
        "name": row['name'],
        "is_enabled": row['is_enabled'],
        "when_condition": row['when_condition'],
        "do_action": row['do_action'],
        "tone": row['tone'],
        "sort_order": row['sort_order'],
        "created_at": row['created_at'].isoformat() if row['created_at'] else None,
        "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None,
    }


def _format_log_entry(row: dict) -> dict:
    return {
        "id": str(row['id']),
        "message_id": row['message_id'],
        "subject": row['subject'],
        "replied_at": row['replied_at'].isoformat() if row['replied_at'] else None,
        "reply_message_id": row['reply_message_id'],
        "status": row['status'],
        "error_message": row['error_message'],
        "llm_model": row['llm_model'],
    }
