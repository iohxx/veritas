from veritas.attestation.canonical import canonical
from veritas.storage.jobs import read_json
from veritas.attestation.verify import check_bundle
from veritas.technocore.sender import publish
from veritas.errors import VeritasError


def process(job,pipeline,client):
    store=pipeline.store
    existing=store.db.execute('SELECT hash,state FROM jobs WHERE id=?',(job.job_id,)).fetchone()
    if existing:
        from veritas.attestation.canonical import digest
        if existing[0]!=digest(canonical(job.model_dump())) or existing[1]!='completed':
            raise VeritasError('duplicate_or_interrupted_job')
        folder=store.job_path(job.job_id)
        attestation=read_json(folder/'attestation.json')
        if check_bundle(attestation,folder/'evidence'):
            raise VeritasError('stored_evidence_invalid')
    else:
        attestation=pipeline.verify(canonical(job.model_dump()))
    return publish(attestation,pipeline.identity,client,store,pipeline.config.max_posts_per_hour)
