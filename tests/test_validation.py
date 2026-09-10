import unittest
from veritas.identity.keys import Identity
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from veritas.attestation.canonical import canonical
from veritas.security.sanitizer import parse_job
from veritas.security.policy import safe_url
from veritas.errors import VeritasError
from veritas.verification.numerical import numerical_checks, run_calculation


def job_dict(claim='The total of 10 + 20 + 30 is 60.', ident='job_test'):
    return {'type':'VERITAS_JOB','version':'1.0','job_id':ident,'requester':Identity(Ed25519PrivateKey.from_private_bytes(bytes(range(32)))).did,'task_type':'research_verification','claim':claim,'sources':[],'submitted_result':claim,'created_at':'2026-09-10T00:00:00Z','nonce':ident}


class ValidationTests(unittest.TestCase):
    def test_valid_and_invalid_jobs(self):
        j = job_dict()
        self.assertEqual(parse_job(canonical(j)).job_id, 'job_test')
        for field, value in [('job_id','../x'),('requester','did:key:fake'),('version','2.0'),('sources',['file:///etc/passwd']),('created_at','today')]:
            with self.subTest(field=field), self.assertRaises(VeritasError):
                parse_job(canonical(dict(j, **{field:value})))
        with self.assertRaises(VeritasError):
            parse_job(canonical(j), 10)

    def test_url_security(self):
        for url in ('http://127.0.0.1','http://[::1]','http://169.254.169.254','http://10.1.2.3','file:///x','https://u:p@example.com','https://example.com:22','https://technocore.chat/r/x/say/a/b'):
            with self.subTest(url=url), self.assertRaises(VeritasError):
                safe_url(url)

    def test_arithmetic(self):
        for total, outcome in [('60','pass'),('61','fail')]:
            job = parse_job(canonical(job_dict(f'The total of 10 + 20 + 30 is {total}.')))
            self.assertEqual(numerical_checks(job)['checks'][0]['outcome'], outcome)
        for op, xs, expected in [('percentage_change',['80','100'],'25'),('mean',['2','4'],'3'),('multiply',['2','3'],'6'),('subtract',['3','1'],'2'),('divide',['1','2'],'0.5'),('ratio',['6','3'],'2'),('compare',['1','2'],'less')]:
            self.assertEqual(run_calculation({'operation':op,'operands':xs,'expected':expected})['outcome'],'pass')
        self.assertEqual(run_calculation({'operation':'divide','operands':['1','0'],'expected':'0'})['outcome'],'unavailable')
        self.assertEqual(run_calculation({'operation':'convert','operands':['2'],'expected':'2000','unit_from':'km','unit_to':'m'})['outcome'],'pass')
        self.assertEqual(run_calculation({'operation':'convert','operands':['2'],'expected':'2000','unit_from':'USD','unit_to':'EUR'})['outcome'],'unavailable')

    def test_no_partial_claim_shortcut(self):
        j = job_dict('The total of 10 + 20 + 30 is 60. Also Earth is flat.')
        self.assertFalse(numerical_checks(parse_job(canonical(j)))['pure_arithmetic'])
        j = job_dict("__import__('os').system('whoami')")
        self.assertEqual(numerical_checks(parse_job(canonical(j)))['checks'], [])
