from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from veritas.attestation.canonical import parse_json
from veritas.identity.did import public_from_did
from veritas.security.policy import safe_id, safe_url
from veritas.errors import VeritasError


class Calculation(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    operation: Literal['add', 'subtract', 'multiply', 'divide', 'percentage_change', 'mean', 'ratio', 'convert', 'compare']
    operands: list[str] = Field(min_length=1, max_length=30)
    expected: str = Field(max_length=100)
    # A calculation proves arithmetic only, not that inputs match the world.
    source_indices: list[int] = Field(default_factory=list, max_length=20)
    unit_from: str = Field(default='', max_length=20)
    unit_to: str = Field(default='', max_length=20)


class Job(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    type: Literal['VERITAS_JOB']
    version: Literal['1.0']
    job_id: str
    requester: str
    task_type: Literal['research_verification']
    claim: str = Field(min_length=1, max_length=8000)
    sources: list[str] = Field(max_length=20)
    submitted_result: str = Field(min_length=1, max_length=16000)
    created_at: str
    nonce: str = Field(min_length=1, max_length=128, pattern=r'^[A-Za-z0-9_-]+$')
    calculations: list[Calculation] = Field(default_factory=list, max_length=30)
    extensions: dict = Field(default_factory=dict)

    @field_validator('job_id')
    @classmethod
    def valid_id(cls, v):
        return safe_id(v)

    @field_validator('requester')
    @classmethod
    def valid_did(cls, v):
        public_from_did(v)
        return v

    @field_validator('sources')
    @classmethod
    def valid_urls(cls, values):
        for value in values:
            safe_url(value)
        return values

    @field_validator('created_at')
    @classmethod
    def valid_date(cls, value):
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            raise ValueError('timezone required')
        return value


def parse_job(raw, maximum=65536):
    try:
        job = Job.model_validate(parse_json(raw, maximum))
        for calc in job.calculations:
            if any(i < 0 or i >= len(job.sources) for i in calc.source_indices):
                raise ValueError()
        return job
    except (ValueError, TypeError) as exc:
        raise VeritasError('invalid_job') from exc
