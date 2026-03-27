from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from src.api.dependencies import get_result_builder
from src.api.schemas import StandardFieldsExportRequest, StandardFieldsExportResponse
from src.api.services import ResultBuilder


router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/standard-fields", response_model=StandardFieldsExportResponse)
def export_standard_fields(
    payload: StandardFieldsExportRequest,
    request: Request,
    result_builder: ResultBuilder = Depends(get_result_builder),
) -> StandardFieldsExportResponse:
    output_path = result_builder.export_custom_table(
        headers=list(payload.headers),
        rows=[list(row) for row in payload.rows],
        filename=payload.filename,
    )
    file_path = Path(output_path)
    return StandardFieldsExportResponse(
        filename=file_path.name,
        download_url=str(
            request.url_for("download_standard_fields_export", filename=file_path.name)
        ),
    )


@router.get(
    "/standard-fields/{filename}",
    name="download_standard_fields_export",
)
def download_standard_fields_export(
    filename: str,
    result_builder: ResultBuilder = Depends(get_result_builder),
) -> FileResponse:
    file_path = result_builder.export_dir / "standard_fields" / filename
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found.")
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
