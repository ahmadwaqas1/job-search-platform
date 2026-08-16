from uuid import UUID

from pydantic import BaseModel


class CVDocumentOut(BaseModel):
    id: UUID
    kind: str
    original_filename: str
    mime_type: str
    parse_status: str
    parse_error: str
    parsed_json: dict | None = None

    model_config = {"from_attributes": True}
