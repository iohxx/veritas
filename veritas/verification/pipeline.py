import time
from veritas.attestation.canonical import canonical, digest
from veritas.attestation.verify import create, check_bundle
from veritas.storage.jobs import write_json, read_json
from veritas.storage.evidence import build_manifest
from veritas.security.sanitizer import parse_job
from veritas.verification.claims import extract_claims
from veritas.verification.numerical import numerical_checks
from veritas.verification.semantic import analyze
from veritas.verification.contradictions import search
from veritas.verification.verdict import decide
from veritas.verification.sources import retrieve


class Pipeline:
    def __init__(self, config, identity, store, provider, retriever=retrieve):
        self.config,self.identity,self.store,self.provider,self.retriever = config,identity,store,provider,retriever

    def verify(self, raw):
        start = time.monotonic()
        job = parse_job(raw,self.config.max_job_size)
        self.store.quota('jobs',self.config.max_jobs_per_hour)
        folder = self.store.reserve(job,digest(canonical(job.model_dump())))
        try:
            evidence = folder/'evidence'
            evidence.mkdir()
            job_data = job.model_dump()
            write_json(folder/'input.json',job_data)
            write_json(evidence/'job.json',job_data)
            write_json(evidence/'claims.json',extract_claims(job))
            sources=[]
            for index,url in enumerate(job.sources):
                source, snapshot = self.retriever(url,self.config)
                if snapshot is not None:
                    name = f'snapshots/{index:03d}.bin'
                    path = evidence/name
                    path.parent.mkdir(exist_ok=True)
                    path.write_bytes(snapshot)
                    source['snapshot']=name
                sources.append(source)
            numerical = numerical_checks(job)
            if numerical['pure_arithmetic']:
                semantic={'performed':False,'reason':'not_applicable_pure_arithmetic','findings':[],'full_claim_supported':False}
            else:
                semantic=analyze(job,sources,self.provider,self.config.max_inference_per_job)
            contradictions=search(sources,semantic)
            for i, source in enumerate(sources):
                source['supports_claim'] = any(f['source_index']==i and f['relation'] in ('direct','indirect') for f in semantic.get('findings',[]))
            checks={'numerical':numerical,'semantic':semantic,'contradictions':contradictions}
            verdict=decide(job,numerical,semantic,contradictions,sources,self.config.weights,self.identity.did)
            write_json(evidence/'sources.json',sources)
            write_json(evidence/'checks.json',checks)
            write_json(evidence/'verdict.json',verdict)
            attestation=create(verdict,build_manifest(evidence),self.identity)
            write_json(evidence/'attestation.json',attestation)
            write_json(folder/'attestation.json',attestation)
            write_json(folder/'verdict.json',verdict)
            write_json(folder/'result.json',{'job_id':job.job_id,'verdict':verdict,'attestation':attestation})
            write_json(self.store.root/'attestations'/f'{job.job_id}.json',attestation)
            self.store.finish(job.job_id,'completed')
            self.store.log('verification_completed',job.job_id,verdict['status'],int((time.monotonic()-start)*1000))
            return attestation
        except Exception:
            self.store.finish(job.job_id,'failed')
            self.store.log('verification_failed',job.job_id)
            raise


def replay(store,job_id):
    folder=store.job_path(job_id)
    evidence=folder/'evidence'
    attestation=read_json(folder/'attestation.json')
    errors=check_bundle(attestation,evidence)
    if errors:
        return errors
    job=parse_job(canonical(read_json(evidence/'job.json')))
    previous=read_json(evidence/'checks.json')['numerical']
    current=numerical_checks(job)
    if previous==current:
        return []
    return [{'field':'numerical','saved':previous,'replayed':current}]
