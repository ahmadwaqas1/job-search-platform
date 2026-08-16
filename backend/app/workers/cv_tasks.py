import asyncio
from pathlib import Path
from uuid import UUID

import structlog

from app.database import get_sync_session
from app.integrations.ollama_client import OllamaError
from app.models.cv import CVDocument
from app.services.cv_parser_service import extract_cv_structured_data
from app.utils.text_extract import UnsupportedFileType, extract_text

log = structlog.get_logger()


def parse_cv_document(cv_document_id: str) -> None:
    with get_sync_session() as db:
        doc = db.get(CVDocument, UUID(cv_document_id))
        if doc is None:
            log.warning("cv.document_not_found", cv_document_id=cv_document_id)
            return

        doc.parse_status = "processing"
        db.commit()

        try:
            raw_text = extract_text(Path(doc.file_path), doc.mime_type)
            if not raw_text.strip():
                raise ValueError("No extractable text found in the uploaded file.")

            doc.raw_extracted_text = raw_text
            structured = asyncio.run(extract_cv_structured_data(raw_text))

            doc.parsed_json = structured
            doc.parse_status = "parsed"
            doc.parse_error = ""
        except (UnsupportedFileType, ValueError, OllamaError) as exc:
            log.warning("cv.parse_failed", cv_document_id=cv_document_id, error=str(exc))
            doc.parse_status = "failed"
            doc.parse_error = str(exc)
        except Exception as exc:  # noqa: BLE001 - surface unexpected errors to the user too
            log.exception("cv.parse_failed_unexpected", cv_document_id=cv_document_id)
            doc.parse_status = "failed"
            doc.parse_error = f"Unexpected error: {exc}"

        db.commit()
