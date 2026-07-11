from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.schemas.common import BaseSchema
from app.schemas.space import SpaceSummary

class FavoriteResponse(BaseSchema):
    id: UUID
    user_id: UUID
    space_id: UUID
    created_at: datetime
    space: Optional[SpaceSummary] = None
