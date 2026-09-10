import time
from veritas.technocore.reader import receive_job
from veritas.agent.worker import process
from veritas.agent.scheduler import backoff
from veritas.errors import VeritasError, NetworkError


def run(pipeline,client,once=False,since=None):
    store=pipeline.store
    key='cursor:'+client.url
    if since is not None:
        store.set(key,since)
    failures=0
    while True:
        cursor=store.get(key,0)
        try:
            response=client.read(cursor,0 if once else 10)
            messages=[m for m in response['messages'] if m['seq']>cursor]
            if messages and messages[0]['seq']>cursor+1:
                raise VeritasError('room_history_gap_set_explicit_since')
            for message in messages:
                try:
                    job=receive_job(client.room,message,pipeline.config.max_job_size)
                    if job is not None:
                        process(job,pipeline,client)
                except NetworkError:
                    raise
                except VeritasError as exc:
                    if str(exc).startswith(('rate_limit','publication_')):
                        raise
                    store.log('job_rejected')
                store.set(key,message['seq'])
            failures=0
            if once:
                return
            if not messages and response.get('wait_held') is False:
                time.sleep(10)
        except VeritasError as exc:
            store.log('agent_operation_failed')
            if once or str(exc).startswith(('room_history_gap','publication_uncertain','publication_rejected')):
                raise
            failures+=1
            time.sleep(backoff(failures))
