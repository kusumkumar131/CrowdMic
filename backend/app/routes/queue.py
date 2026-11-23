from fastapi import APIRouter, HTTPException, Depends, status
from app.routes.auth import get_current_user
from app.services.queue_service import add_to_queue, get_session_queue, cancel_user_hand

router = APIRouter(prefix="/sessions/{session_id}/queue", tags=["queue"])

@router.get("")
async def get_queue(session_id: str, current_user: dict = Depends(get_current_user)):
    queue = await get_session_queue(session_id)
    return queue

@router.post("")
async def join_queue(session_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can enter the speaking queue")
    try:
        user_id = current_user.get("id") or str(current_user.get("_id"))
        entry = await add_to_queue(
            session_id=session_id,
            user_id=user_id,
            user_name=current_user.get("name"),
            user_role=current_user.get("role")
        )
        try:
            from app.websocket.events import broadcast_queue_update
            await broadcast_queue_update(session_id)
        except Exception:
            pass
        return entry
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("")
async def leave_queue(session_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("id") or str(current_user.get("_id"))
    success = await cancel_user_hand(session_id, user_id)
    try:
        from app.websocket.events import broadcast_queue_update
        await broadcast_queue_update(session_id)
    except Exception:
        pass
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hand request not found in queue")
    return {"message": "Hand request cancelled"}
