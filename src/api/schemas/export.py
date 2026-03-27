from typing import List

from pydantic import BaseModel, Field, field_validator, model_validator


class StandardFieldsExportRequest(BaseModel):
    headers: List[str]
    rows: List[List[str]]
    filename: str = Field(default="standard_fields_export.xlsx")

    @field_validator("headers")
    @classmethod
    def validate_headers(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("headers must not be empty.")
        normalized = [item.strip() for item in value]
        if any(not item for item in normalized):
            raise ValueError("headers must not contain blank values.")
        return normalized

    @field_validator("rows")
    @classmethod
    def validate_rows(cls, value: List[List[str]]) -> List[List[str]]:
        if not value:
            raise ValueError("rows must not be empty.")
        return value

    @model_validator(mode="after")
    def validate_row_lengths(self) -> "StandardFieldsExportRequest":
        expected = len(self.headers)
        invalid = [index for index, row in enumerate(self.rows, start=1) if len(row) != expected]
        if invalid:
            raise ValueError("row length must match headers length.")
        return self


class StandardFieldsExportResponse(BaseModel):
    filename: str
    download_url: str
