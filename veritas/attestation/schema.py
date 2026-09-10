from typing import Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from veritas.identity.did import public_from_did
from veritas.security.policy import safe_id


class Attestation(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    type: Literal['VERITAS_ATTESTATION']
    version: Literal['1.0']
    canonicalization: Literal['VERITAS-C14N-1']
    job_id: str
    status: Literal['VERIFIED','PARTIALLY_VERIFIED','UNVERIFIED','CONTRADICTED','INSUFFICIENT_EVIDENCE']
    confidence: int = Field(ge=0, le=100)
    evidence_hash: str = Field(pattern=r'^sha256:[a-f0-9]{64}$')
    verifier: str
    timestamp: str
    signature: str = Field(pattern=r'^[A-Za-z0-9_-]{86}$')

    @field_validator('job_id')
    @classmethod
    def id_valid(cls,v): return safe_id(v)

    @field_validator('verifier')
    @classmethod
    def did_valid(cls,v):
        public_from_did(v)
        return v

    @field_validator('timestamp')
    @classmethod
    def timestamp_valid(cls,v):
        if datetime.fromisoformat(v.replace('Z','+00:00')).tzinfo is None:
            raise ValueError()
        return v
