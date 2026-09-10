from veritas.errors import VeritasError


class ProcessLock:
    def __init__(self,root):
        self.path=root/'process.lock'
        self.file=None

    def __enter__(self):
        import os
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.file=self.path.open('a+b')
        if self.path.stat().st_size == 0:
            self.file.write(b'0')
            self.file.flush()
        self.file.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise VeritasError('another_veritas_process_is_running')
        return self

    def __exit__(self,*args):
        self.file.close()
