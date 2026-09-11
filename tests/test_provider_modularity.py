import unittest
from unittest.mock import patch

from tests import test_technocore as technocore_tests
from tests.test_validation import job_dict
from veritas.agent.daemon import run
from veritas.attestation.canonical import canonical, digest
from veritas.attestation.verify import check_bundle
from veritas.config import Config
from veritas.errors import VeritasError
from veritas.identity.signing import sign
from veritas.inference.base import InferenceProvider, UnavailableProvider
from veritas.inference.factory import provider_for
from veritas.storage.jobs import read_json
from veritas.verification.pipeline import replay


class EvidenceProvider(InferenceProvider):
    """Controlled test adapter, not a real inference service."""
    def generate(self, prompt, context):
        return {'full_claim_supported': True, 'findings': [{
            'source_index': 0, 'relation': 'direct',
            'quote': context['sources'][0]['text'], 'reason': 'Exact fixture'}],
            'reason': 'Supported by the controlled fixture'}


class AlternateProvider(EvidenceProvider):
    pass


class ProviderConfigurationTests(unittest.TestCase):
    def test_default_has_no_inference_dependency(self):
        with patch.dict('os.environ', {}, clear=True):
            self.assertIsInstance(provider_for(Config.from_env()), UnavailableProvider)

    def test_explicit_adapters_and_unknown_provider(self):
        self.assertEqual(type(provider_for(Config(inference_provider='ollama'))).__name__,
                         'LocalInferenceProvider')
        external = Config(inference_provider='external',
                          inference_url='https://example.com/api/chat', model='operator-model')
        self.assertEqual(type(provider_for(external)).__name__, 'ExternalInferenceProvider')
        with self.assertRaisesRegex(VeritasError, 'unknown_inference_provider'):
            provider_for(Config(inference_provider='unknown'))


class AutonomousModularityTests(unittest.TestCase):
    setUp = technocore_tests.TechnocoreTests.setUp
    tearDown = technocore_tests.TechnocoreTests.tearDown

    def process_signed_job(self, provider, claim, expected):
        self.pipeline.provider = provider
        job = job_dict(claim)
        job['requester'] = self.identity.did
        job['sources'] = ['https://example.com/evidence']
        raw = b'The service supports signed messages.'
        self.pipeline.retriever = lambda url, config: ({
            'url': url, 'accessible': True, 'usable': True,
            'text': raw.decode(), 'sha256': digest(raw)}, raw)
        text = canonical(job).decode()
        self.service.messages.append({
            'seq': 1, 'from': self.identity.did, 'nonce': 1, 'text': text,
            'sig': sign(self.identity.key, f'veritas|1|{text}'.encode())})
        run(self.pipeline, self.client, once=True)
        folder = self.store.job_path(job['job_id'])
        att = read_json(folder / 'attestation.json')
        self.assertEqual(att['status'], expected)
        self.assertEqual(att['verifier'], self.identity.did)
        self.assertEqual(check_bundle(att, folder / 'evidence'), [])
        self.assertEqual(replay(self.store, job['job_id']), [])
        self.assertEqual(self.service.posts, 1)
        run(self.pipeline, self.client, once=True)
        self.assertEqual(self.service.posts, 1, 'No duplicate attestation')
        return read_json(folder / 'evidence' / 'checks.json')['semantic']

    def test_research_without_inference_still_attests(self):
        result = self.process_signed_job(UnavailableProvider(),
            'The service supports signed messages.', 'INSUFFICIENT_EVIDENCE')
        self.assertFalse(result['performed'])
        self.assertEqual(result['reason'], 'inference_disabled')

    def test_arithmetic_never_calls_provider(self):
        provider = EvidenceProvider()
        with patch.object(provider, 'generate', side_effect=AssertionError('Inference called')):
            self.process_signed_job(provider, 'The total of 10 + 20 + 30 is 60.', 'VERIFIED')

    def test_custom_provider_without_core_changes(self):
        result = self.process_signed_job(EvidenceProvider(),
            'The service supports signed messages.', 'VERIFIED')
        self.assertEqual(result['provider'], 'EvidenceProvider')

    def test_replacement_provider_without_core_changes(self):
        result = self.process_signed_job(AlternateProvider(),
            'The service supports signed messages.', 'VERIFIED')
        self.assertEqual(result['provider'], 'AlternateProvider')
