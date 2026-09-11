import argparse
import json
import sqlite3
from pathlib import Path
from veritas.config import Config
from veritas.identity.keys import Identity
from veritas.storage.jobs import Store, read_json
from veritas.security.limits import ProcessLock
from veritas.inference.factory import provider_for
from veritas.verification.pipeline import Pipeline, replay
from veritas.attestation.verify import check_bundle
from veritas.technocore.client import TechnocoreClient
from veritas.technocore.sender import publish
from veritas.agent.daemon import run
from veritas.errors import VeritasError


def main(argv=None):
    parser=argparse.ArgumentParser(prog='veritas',description='Independent evidence verification and signed attestations')
    parser.add_argument('--data-dir',type=Path)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('init')
    sub.add_parser('identity')
    v=sub.add_parser('verify'); v.add_argument('job',type=Path); v.add_argument('--publish',action='store_true')
    r=sub.add_parser('replay'); r.add_argument('job_id')
    i=sub.add_parser('inspect'); i.add_argument('job_id')
    a=sub.add_parser('verify-attestation'); a.add_argument('attestation',type=Path); a.add_argument('--evidence',type=Path)
    a=sub.add_parser('agent'); a.add_argument('--once',action='store_true'); a.add_argument('--since',type=int)
    p=sub.add_parser('publish'); p.add_argument('job_id')
    args=parser.parse_args(argv)
    try:
        if args.command=='verify-attestation':
            att=read_json(args.attestation,65536)
            folder=args.evidence or (args.attestation.parent if (args.attestation.parent/'manifest.json').exists() else args.attestation.parent/'evidence')
            errors=check_bundle(att,folder)
            print('INVALID ATTESTATION' if errors else 'VALID ATTESTATION')
            if errors: print(json.dumps(errors))
            return 1 if errors else 0
        config=Config.from_env()
        if args.data_dir is not None: config.data_dir=args.data_dir
        config.data_dir=config.data_dir.resolve()
        with ProcessLock(config.data_dir):
            if args.command in ('init','identity'):
                identity=Identity.load(config.data_dir,create=args.command=='init')
                print(f'VERITAS IDENTITY\nDID:\n{identity.did}\nPrivate key:\nLOCAL ONLY\nStatus:\nREADY')
                return 0
            store=Store(config.data_dir)
            try:
                if args.command=='inspect':
                    print(json.dumps(read_json(store.job_path(args.job_id)/'result.json'),indent=2,ensure_ascii=True))
                    return 0
                if args.command=='replay':
                    differences=replay(store,args.job_id)
                    print('REPLAY DIFFERENCE' if differences else 'REPLAY SUCCESS')
                    if differences: print(json.dumps(differences,ensure_ascii=True))
                    return 1 if differences else 0
                identity=Identity.load(config.data_dir)
                client=TechnocoreClient(config.technocore_url,config.room,config.request_timeout)
                if args.command=='publish':
                    folder=store.job_path(args.job_id)
                    attestation=read_json(folder/'attestation.json')
                    if check_bundle(attestation,folder/'evidence'):
                        raise VeritasError('evidence_integrity_failed')
                    print(json.dumps(publish(attestation,identity,client,store,config.max_posts_per_hour)))
                    return 0
                pipeline=Pipeline(config,identity,store,provider_for(config))
                if args.command=='agent':
                    run(pipeline,client,args.once,args.since)
                    return 0
                with args.job.open('rb') as f:
                    attestation=pipeline.verify(f.read(config.max_job_size+1))
                analysis=read_json(store.job_path(attestation['job_id'])/'evidence'/'checks.json')['semantic']
                if not analysis.get('performed') and analysis.get('reason')!='not_applicable_pure_arithmetic':
                    print('SEMANTIC ANALYSIS NOT PERFORMED: '+analysis.get('reason','unknown'))
                print(json.dumps(attestation,indent=2))
                if args.publish:
                    print(json.dumps(publish(attestation,identity,client,store,config.max_posts_per_hour)))
                return 0
            finally:
                store.close()
    except VeritasError as exc:
        print('ERROR: '+str(exc))
        return 2
    except (OSError,ValueError,sqlite3.Error):
        print('ERROR: local_operation_failed')
        return 2
    except KeyboardInterrupt:
        print('STOPPED')
        return 130


if __name__=='__main__':
    raise SystemExit(main())
