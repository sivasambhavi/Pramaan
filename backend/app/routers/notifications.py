import os
import logging
from fastapi import APIRouter, Form, Request
from pydantic import BaseModel
from app.neo4j_client import get_session
from twilio.rest import Client

logger = logging.getLogger(__name__)

router = APIRouter()

class NotificationTrigger(BaseModel):
    asset_id: str
    message_template: str

@router.post("/trigger")
def trigger_street_notification(payload: NotificationTrigger):
    """
    Simulates sending a Micro-Accountability WhatsApp/SMS push to all opted-in residents
    on the street where an Asset just received Verified Proof.
    """
    query = """
    MATCH (a:Asset {asset_id: $asset_id})-[:LOCATED_IN]->(street:Region {type: 'street'})
    MATCH (res:Resident {opt_in: true})-[:RESIDES_ON]->(street)
    OPTIONAL MATCH (e_after:Evidence {before_or_after: 'after'})-[:PROVES]->(a)
    OPTIONAL MATCH (e_before:Evidence {before_or_after: 'before'})-[:PROVES]->(a)
    RETURN 
        a.name AS asset_name,
        street.name AS street_name,
        collect(DISTINCT res.phone) AS phones,
        count(DISTINCT res) AS resident_count,
        e_after.url_or_path AS after_photo,
        e_before.url_or_path AS before_photo
    """
    
    try:
        with get_session() as session:
            results = session.run(query, asset_id=payload.asset_id).data()
        
        if not results:
            return {"success": False, "message": "Asset not found or no opted-in residents on that street."}
            
        record = results[0]
        resident_count = record.get("resident_count", 0)
        
        if resident_count == 0:
             return {"success": False, "message": f"No opted-in residents on {record.get('street_name')}."}
             
        # Real Twilio Integration
        twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_auth = os.environ.get("TWILIO_AUTH_TOKEN")
        twilio_from = os.environ.get("TWILIO_FROM_NUMBER")
        
        tw_success_count = 0
        if twilio_sid and twilio_auth and twilio_from:
            try:
                client = Client(twilio_sid, twilio_auth)
                for phone in record.get("phones", []):
                    # Ensure phone is in E.164 format for WhatsApp sandbox
                    # Format: whatsapp:+919999999999
                    to_number = f"whatsapp:{phone}" if not str(phone).startswith('whatsapp:') else phone
                    from_number = f"whatsapp:{twilio_from}"
                    
                    msg_body = payload.message_template.format(
                        asset_name=record["asset_name"],
                        street_name=record["street_name"]
                    )
                    
                    message = client.messages.create(
                        from_=from_number,
                        body=msg_body,
                        to=to_number
                    )
                    logger.info(f"Sent WhatsApp to {to_number}: {message.sid}")
                    tw_success_count += 1
            except Exception as tw_err:
                logger.error(f"Twilio error: {tw_err}")
                return {"success": False, "message": f"Graph match succeeded but Twilio failed: {tw_err}"}
        
        return {
             "success": True,
             "notification_id": f"BLAST_{payload.asset_id[:8]}",
             "asset_name": record["asset_name"],
             "street_name": record["street_name"],
             "recipients_found": resident_count,
             "whatsapp_sent": tw_success_count,
             "evidence_included": {
                 "before": record.get("before_photo"),
                 "after": record.get("after_photo")
             },
             "message": "Push notifications dispatched successfully."
        }
        
    except Exception as e:
        logger.error(f"Error triggering notifications for {payload.asset_id}: {e}")
        return {"success": False, "error": str(e)}

@router.post("/webhook/whatsapp")
async def inbound_whatsapp_media(
    request: Request,
    NumMedia: int = Form(0),
    MediaUrl0: str = Form(None),
    MediaContentType0: str = Form(None),
    From: str = Form(...)
):
    """
    Inbound Twilio Webhook: Listens for WhatsApp messages.
    If the message contains a media attachment (PDF, Image), it automatically
    downloads it to the local /inbox/ folder for the PRAMAAN pipeline to ingest.
    """
    import os
    import requests
    from datetime import datetime
    
    if NumMedia == 0 or not MediaUrl0:
        return {"success": True, "message": "No media found in the message."}

    # Determine extension
    ext = ".bin"
    if MediaContentType0 == "application/pdf":
        ext = ".pdf"
    elif MediaContentType0 == "image/jpeg":
        ext = ".jpg"
    elif MediaContentType0 == "image/png":
        ext = ".png"
        
    # Download the media
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_auth = os.environ.get("TWILIO_AUTH_TOKEN")
    auth_tuple = (twilio_sid, twilio_auth) if twilio_sid and twilio_auth else None
    
    # Safe filename calculation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_phone = From.replace("whatsapp:", "").replace("+", "")
    filename = f"whatsapp_{safe_phone}_{timestamp}{ext}"
    
    # Target inbox path (e:/INDIA_INNOVATES/Pramaan/inbox)
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    repo_root = os.path.dirname(backend_dir)
    inbox_dir = os.path.join(repo_root, "inbox")
    os.makedirs(inbox_dir, exist_ok=True)
    save_path = os.path.abspath(os.path.join(inbox_dir, filename))
    
    try:
        r = requests.get(MediaUrl0, auth=auth_tuple, stream=True, timeout=15)
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logger.info(f"Successfully downloaded WhatsApp media to {save_path}")
        return {"success": True, "message": "Media successfully routed to PRAMAAN inbox."}
    except Exception as e:
        logger.error(f"Failed to download Twilio media: {e}")
        return {"success": False, "error": str(e)}

