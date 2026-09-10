from pathlib import Path, PurePosixPath
import re
from veritas.attestation.schema import Attestation
from veritas.attestation.canonical import canonical, digest
from veritas.identity.signing import verify, sign
from veritas.storage.jobs import read_json
from veritas.errors import VeritasError


def create(verdict, evidence_hash, identity):
    payload = {'type':'VERITAS_ATTESTATION','version':'1.0','canonicalization':'VERITAS-C14N-1','job_id':verdict['job_id'],'status':verdict['status'],'confidence':verdict['confidence'],'evidence_hash':evidence_hash,'verifier':identity.did,'timestamp':verdict['timestamp']}
    return dict(payload, signature=sign(identity.key, canonical(payload)))


def verify_signature(attestation):
    try:
        parsed = Attestation.model_validate(attestation)
        payload = parsed.model_dump(exclude={'signature'})
        return verify(parsed.verifier, parsed.signature, canonical(payload))
    except (ValueError, VeritasError, TypeError):
        return False


def check_bundle(attestation, folder):
    errors = []
    folder = Path(folder)
    if not verify_signature(attestation):
        return ['invalid_signature_or_attestation']
    try:
        manifest = read_json(folder/'manifest.json')
        if digest(canonical(manifest)) != attestation['evidence_hash']:
            return ['manifest_hash_mismatch']
        if set(manifest) != {'type','version','files'} or manifest['type'] != 'VERITAS_EVIDENCE_MANIFEST' or manifest['version'] != '1.0':
            return ['invalid_manifest']
        files = manifest['files']
        if not isinstance(files,dict) or len(files)>100 or not {'job.json','sources.json','checks.json','verdict.json'}.issubset(files):
            return ['missing_required_evidence']
        for name, expected in files.items():
            p = PurePosixPath(name)
            if not isinstance(expected,str) or not re.fullmatch(r'sha256:[a-f0-9]{64}',expected) or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name or p.as_posix()!=name:
                errors.append('unsafe_manifest_entry')
                continue
            path = folder/name
            if any(part.is_symlink() or part.is_junction() for part in [path,*path.parents]):
                errors.append('unsafe_evidence_link:' + name)
                continue
            if not path.resolve().is_relative_to(folder.resolve()):
                errors.append('unsafe_evidence_path')
                continue
            if not path.is_file():
                errors.append('missing_file:' + name)
            elif path.stat().st_size>8000000 or digest(path.read_bytes())!=expected:
                errors.append('file_hash_mismatch:' + name)
        if errors:
            return errors
        job, verdict = read_json(folder/'job.json'), read_json(folder/'verdict.json')
        if job['job_id'] != attestation['job_id']:
            errors.append('job_id_mismatch')
        for field in ('job_id','status','confidence','verifier','timestamp'):
            if verdict.get(field)!=attestation[field]:
                errors.append('verdict_mismatch:' + field)
        sources = read_json(folder/'sources.json')
        for source in sources:
            if source.get('snapshot') and files.get(source['snapshot'])!=source.get('sha256'):
                errors.append('snapshot_hash_reference_mismatch')
        return errors
    except (OSError, ValueError, VeritasError, KeyError, TypeError, AttributeError):
        return ['unreadable_or_invalid_evidence']
