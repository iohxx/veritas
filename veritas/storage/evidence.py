from pathlib import Path
from veritas.attestation.canonical import canonical, digest
from veritas.storage.jobs import write_json


def build_manifest(folder):
    files = {}
    for path in sorted(Path(folder).rglob('*')):
        if path.is_file() and path.name not in ('manifest.json','attestation.json'):
            files[path.relative_to(folder).as_posix()] = digest(path.read_bytes())
    manifest = {'type':'VERITAS_EVIDENCE_MANIFEST','version':'1.0','files':files}
    write_json(Path(folder)/'manifest.json',manifest)
    return digest(canonical(manifest))
