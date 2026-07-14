"""
WebSocket endpoints
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_ws
from app.websockets.chat import (
    manager,
    handle_chat_message,
    handle_typing_indicator,
    handle_message_read
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint para chat em tempo real
    
    Requer token JWT como query parameter: /ws/chat?token=xxx
    
    Mensagens suportadas:
    - send_message: Envia mensagem de chat
    - typing: Indica que usuário está digitando
    - read: Marca mensagens como lidas
    """
    # Autentica usuário
    try:
        current_user = await get_current_user_ws(token=token, db=db)
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # Conecta
    await manager.connect(websocket, current_user.id)
    
    try:
        while True:
            # Recebe mensagem do cliente
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "send_message":
                await handle_chat_message(data, current_user.id, db)
            
            elif message_type == "typing":
                await handle_typing_indicator(data, current_user.id, db)
            
            elif message_type == "read":
                await handle_message_read(data, current_user.id, db)
            
            elif message_type == "ping":
                # Keep-alive
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, current_user.id)
        logger.info(f"User {current_user.id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {current_user.id}: {e}")
        manager.disconnect(websocket, current_user.id)
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass


@router.get("/ws/online-users")
async def get_online_users(current_user: User = Depends(get_current_user_ws)):
    """
    Retorna lista de IDs de usuários online
    """
    online_user_ids = list(manager.active_connections.keys())
    return {
        "online_users": online_user_ids,
        "total": len(online_user_ids)
    }
