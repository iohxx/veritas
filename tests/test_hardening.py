import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from veritas.attestation.canonical import canonical
from veritas.attestation.verify import create,check_bundle
from veritas.storage.jobs import read_json,write_json
from veritas.storage.evidence import build_manifest
from veritas.verification.numerical import numerical_checks
from veritas.security.sanitizer import parse_job
from veritas.inference.local import LocalInferenceProvider
from veritas.cli import main
from veritas.errors import VeritasError,NetworkError
from tests.test_validation import job_dict
from tests import test_pipeline as pipeline_tests


class HardeningTests(unittest.TestCase):
    def test_submitted_result_is_not_ignored(self):
        j=job_dict()
        j['submitted_result']='The total of 10 + 20 + 30 is 61.'
        checks=numerical_checks(parse_job(canonical(j)))
        self.assertFalse(checks['pure_arithmetic'])
        self.assertEqual(checks['checks'][-1]['outcome'],'fail')

    def test_ollama_missing_no_fallback(self):
        with patch('veritas.inference.local.request',side_effect=NetworkError()):
            with self.assertRaisesRegex(VeritasError,'ollama_unavailable'):
                LocalInferenceProvider().generate('analyze',{'claim':'x'})

    def test_bad_provider_url_and_unicode(self):
        with self.assertRaises(VeritasError): LocalInferenceProvider(url='http://example.com/api/chat')
        with self.assertRaises(VeritasError): canonical({'a':'\ud800'})

    def test_cli_missing_evidence_is_invalid(self):
        with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()) as out:
            p=Path(d)/'attestation.json'
            p.write_text('{}')
            self.assertEqual(main(['verify-attestation',str(p)]),1)
            self.assertIn('INVALID ATTESTATION',out.getvalue())


class BundleHardeningTests(unittest.TestCase):
    setUp = pipeline_tests.PipelineTests.setUp
    tearDown = pipeline_tests.PipelineTests.tearDown
    def test_signed_manifest_path_traversal(self):
        att=self.pipeline.verify(canonical(job_dict()))
        folder=self.store.job_path('job_test')/'evidence'
        manifest=read_json(folder/'manifest.json')
        manifest['files']['../outside']='sha256:'+'0'*64
        write_json(folder/'manifest.json',manifest)
        from veritas.attestation.canonical import digest
        att=create(read_json(folder/'verdict.json'),digest(canonical(manifest)),self.identity)
        self.assertIn('unsafe_manifest_entry',check_bundle(att,folder))

    def test_signed_but_mismatched_job_id(self):
        self.pipeline.verify(canonical(job_dict()))
        folder=self.store.job_path('job_test')/'evidence'
        job=read_json(folder/'job.json'); job['job_id']='job_changed'
        write_json(folder/'job.json',job)
        att=create(read_json(folder/'verdict.json'),build_manifest(folder),self.identity)
        self.assertIn('job_id_mismatch',check_bundle(att,folder))

    def test_replay_reports_reproducible_difference(self):
        self.pipeline.verify(canonical(job_dict()))
        folder=self.store.job_path('job_test')/'evidence'
        checks=read_json(folder/'checks.json')
        checks['numerical']['checks'][0]['actual']='59'
        write_json(folder/'checks.json',checks)
        att=create(read_json(folder/'verdict.json'),build_manifest(folder),self.identity)
        write_json(folder.parent/'attestation.json',att)
        from veritas.verification.pipeline import replay
        differences=replay(self.store,'job_test')
        self.assertEqual(differences[0]['field'],'numerical')
        self.assertEqual(differences[0]['replayed']['checks'][0]['actual'],'60')
