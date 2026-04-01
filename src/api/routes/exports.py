from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from src.api.dependencies import get_export_file_registry, get_result_builder
from src.api.schemas import StandardFieldsExportRequest, StandardFieldsExportResponse
from src.api.services import ExportFileRegistry, ExportRegistryError, ResultBuilder


router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/standard-fields", response_model=StandardFieldsExportResponse)
def export_standard_fields(
    payload: StandardFieldsExportRequest,
    request: Request,
    result_builder: ResultBuilder = Depends(get_result_builder),
    export_file_registry: ExportFileRegistry = Depends(get_export_file_registry),
) -> StandardFieldsExportResponse:
    output_path = result_builder.export_custom_table(
        headers=list(payload.headers),
        rows=[list(row) for row in payload.rows],
        filename=payload.filename,
    )
    file_path = Path(output_path)
    try:
        export_id = export_file_registry.register_standard_fields_export(file_path.name)
    except ExportRegistryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to register export file.",
        ) from exc
    return StandardFieldsExportResponse(
        export_id=export_id,
        filename=file_path.name,
        download_url=str(
            request.url_for("download_standard_fields_export", export_id=export_id)
        ),
    )


@router.get(
    "/standard-fields/{export_id}",
    name="download_standard_fields_export",
)
def download_standard_fields_export(
    export_id: str,
    result_builder: ResultBuilder = Depends(get_result_builder),
    export_file_registry: ExportFileRegistry = Depends(get_export_file_registry),
) -> FileResponse:
    try:
        filename = export_file_registry.resolve_standard_fields_export(export_id)
    except ExportRegistryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to resolve export file.",
        ) from exc
    if not filename:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found.")
    file_path = result_builder.export_dir / "standard_fields" / filename
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found.")
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
