import firebase_admin
from firebase_admin import credentials, messaging
import os
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Firebase App
_firebase_initialized = False

def init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return
        
    import json
    
    # 1. Tentar ler do JSON direto da env var
    cred_json = getattr(settings, "FIREBASE_CREDENTIALS_JSON", None)
    if cred_json:
        try:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            logger.info("Firebase Admin SDK initialized successfully from JSON env var.")
            return
        except Exception as e:
            logger.error(f"Failed to initialize Firebase from JSON env var: {e}")
            
    # 2. Fallback para arquivo físico
    cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", None)
    if not cred_path or not os.path.exists(cred_path):
        logger.warning(f"Firebase credentials not found (env var or path {cred_path}). Push notifications disabled.")
        return
        
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin SDK initialized successfully from file.")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK from file: {e}")

# Try to initialize at module import, but it's safe if it fails (will just warn)
init_firebase()

class FirebaseService:
    @staticmethod
    def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None) -> bool:
        if not _firebase_initialized:
            logger.warning("Attempted to send push notification, but Firebase is not initialized.")
            return False
            
        if not fcm_token:
            logger.warning("Attempted to send push notification without FCM token.")
            return False
        
        # Valida dados de entrada
        if not title or not body:
            logger.error("Title and body are required for push notifications.")
            return False
            
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title[:100],  # Limita título
                    body=body[:500],    # Limita corpo
                ),
                data={k: str(v) for k, v in (data or {}).items()},  # Converte valores para string
                token=fcm_token,
            )
            response = messaging.send(message)
            logger.info(f"Successfully sent message: {response}")
            return True
        except messaging.UnregisteredError:
            logger.warning(f"FCM token is invalid or unregistered: {fcm_token[:20]}...")
            raise ValueError("Invalid FCM token")
        except messaging.SenderIdMismatchError:
            logger.error("Sender ID mismatch. Check Firebase configuration.")
            return False
        except messaging.QuotaExceededError:
            logger.error("FCM quota exceeded. Try again later.")
            return False
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
