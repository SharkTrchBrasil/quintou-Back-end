from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        from_attributes=True
    )

class PaginatedResponse(BaseSchema, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
class ErrorResponse(BaseSchema):
    detail: str
    code: Optional[str] = None
