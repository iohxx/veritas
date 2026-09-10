import tempfile
import unittest
from pathlib import Path
from veritas.config import Config
from veritas.identity.keys import Identity
from veritas.storage.jobs import Store, read_json
from veritas.attestation.canonical import canonical, digest
from veritas.attestation.verify import check_bundle, verify_signature
from veritas.verification.pipeline import Pipeline, replay
from veritas.inference.base import UnavailableProvider
from veritas.errors import VeritasError
from tests.test_validation import job_dict


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.store=Store(self.root)
        self.config=Config(data_dir=self.root)
        self.identity=Identity.load(self.root,create=True)
        def inaccessible(url, config):
            return {'url':url,'accessible':False,'usable':False,'text':'','reason':'network_failure:404'},None
        self.pipeline=Pipeline(self.config,self.identity,self.store,UnavailableProvider(),inaccessible)
    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_three_examples_and_replay(self):
        for i,claim,status in [(1,'The total of 10 + 20 + 30 is 60.','VERIFIED'),(2,'The total of 10 + 20 + 30 is 61.','CONTRADICTED'),(3,'X is true.','INSUFFICIENT_EVIDENCE')]:
            j=job_dict(claim,f'job_demo{i}')
            if i==3: j['sources']=['https://example.com/missing']
            att=self.pipeline.verify(canonical(j))
            self.assertEqual(att['status'],status)
            self.assertTrue(verify_signature(att))
            self.assertEqual(check_bundle(att,self.store.job_path(j['job_id'])/'evidence'),[])
            self.assertEqual(replay(self.store,j['job_id']),[])

    def test_tampering_and_duplicates(self):
        j=job_dict()
        att=self.pipeline.verify(canonical(j))
        for field,value in [('job_id','job_altered'),('timestamp','2026-01-01T00:00:00Z'),('status','UNVERIFIED'),('confidence',0),('evidence_hash','sha256:'+'0'*64),('signature','A'*86)]:
            self.assertFalse(verify_signature(dict(att,**{field:value})))
        with self.assertRaises(VeritasError): self.pipeline.verify(canonical(j))
        j['job_id']='job_different'
        with self.assertRaises(VeritasError): self.pipeline.verify(canonical(j))
        folder=self.store.job_path('job_test')/'evidence'
        (folder/'checks.json').write_text('{}')
        self.assertIn('file_hash_mismatch:checks.json',check_bundle(att,folder))
        self.assertIn('file_hash_mismatch:checks.json',replay(self.store,'job_test'))

    def test_source_retrieval_not_equal_support(self):
        j=job_dict('The moon is cheese.')
        j['sources']=['https://example.com']
        def retrieve(url,config):
            raw=b'Unrelated page'
            return {'url':url,'accessible':True,'usable':True,'text':raw.decode(),'sha256':digest(raw)},raw
        self.pipeline.retriever=retrieve
        att=self.pipeline.verify(canonical(j))
        self.assertEqual(att['status'],'INSUFFICIENT_EVIDENCE')
        sources=read_json(self.store.job_path(j['job_id'])/'evidence'/'sources.json')
        self.assertFalse(sources[0]['supports_claim'])

    def test_persistent_rate_limit(self):
        self.store.quota('test',1)
        with self.assertRaises(VeritasError): self.store.quota('test',1)
        self.store.close()
        self.store=Store(self.root)
        with self.assertRaises(VeritasError): self.store.quota('test',1)
