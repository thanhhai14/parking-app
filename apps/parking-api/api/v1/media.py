from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import os
from datetime import datetime, timezone
from pydantic import BaseModel

from core.database import get_db_session
from core.s3 import minio_client
from models.media import MediaFile
from api.deps import get_current_user
from models.user import User

router = APIRouter()

class MediaResponse(BaseModel):
    id: uuid.UUID
    bucket: str
    object_key: str
    file_name: str
    mime_type: str
    file_size: int
    media_type: str
    presigned_url: str

@router.post("/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    media_type: str = Form("image"), # image, video, snapshot, thumbnail
    source_type: str = Form(None), # parking_session, vehicle, owner, camera
    source_id: uuid.UUID = Form(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No file uploaded"
        )
        
    file_data = await file.read()
    file_size = len(file_data)
    file_name = file.filename
    mime_type = file.content_type or "application/octet-stream"
    
    # Generate unique object key path: yyyy/mm/dd/media_type/uuid.ext
    now = datetime.now(timezone.utc)
    date_path = now.strftime("%Y/%m/%d")
    unique_id = uuid.uuid4()
    extension = os.path.splitext(file_name)[1]
    object_key = f"{date_path}/{media_type}/{unique_id}{extension}"
    
    # Upload bytes to MinIO
    upload_success = minio_client.upload_bytes(
        file_data=file_data,
        object_key=object_key,
        content_type=mime_type
    )
    
    if not upload_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage"
        )
        
    # Save metadata record in DB
    media_record = MediaFile(
        id=unique_id,
        bucket=minio_client.bucket_name,
        object_key=object_key,
        file_name=file_name,
        mime_type=mime_type,
        file_size=file_size,
        media_type=media_type,
        source_type=source_type,
        source_id=source_id,
        created_by=current_user.id
    )
    
    db.add(media_record)
    
    # Generate pre-signed URL for client access
    presigned_url = minio_client.get_presigned_url(object_key)
    
    return MediaResponse(
        id=media_record.id,
        bucket=media_record.bucket,
        object_key=media_record.object_key,
        file_name=media_record.file_name,
        mime_type=media_record.mime_type,
        file_size=media_record.file_size,
        media_type=media_record.media_type,
        presigned_url=presigned_url or ""
    )
