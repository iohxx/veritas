import csv
import ctypes
import os
import subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from veritas.errors import VeritasError
from veritas.identity.did import did_from_public


def protect_windows(folder):
    """Fixed local utilities only; no shell and no job-controlled arguments."""
    system = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32'
    options = {'capture_output': True, 'check': True, 'creationflags': subprocess.CREATE_NO_WINDOW}
    try:
        result = subprocess.run([str(system / 'whoami.exe'), '/user', '/fo', 'csv', '/nh'], **options)
        sid = next(csv.reader([result.stdout.decode().strip()]))[1]
        # Replace the whole DACL, including pre-existing explicit grants.
        advapi = ctypes.WinDLL('advapi32', use_last_error=True)
        convert = advapi.ConvertStringSecurityDescriptorToSecurityDescriptorW
        convert.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
        convert.restype = ctypes.c_int
        descriptor = ctypes.c_void_p()
        flags = 'OICI' if folder.is_dir() else ''
        if not convert(f'D:P(A;{flags};FA;;;{sid})', 1, ctypes.byref(descriptor), None):
            raise VeritasError('local_key_protection_failed')
        try:
            setter = advapi.SetFileSecurityW
            setter.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_void_p]
            setter.restype = ctypes.c_int
            if not setter(str(folder), 0x80000004, descriptor):
                raise VeritasError('local_key_protection_failed')
        finally:
            free = ctypes.WinDLL('kernel32').LocalFree
            free.argtypes = [ctypes.c_void_p]
            free(descriptor)
    except (OSError, subprocess.SubprocessError, ValueError, IndexError) as exc:
        raise VeritasError('local_key_protection_failed') from exc


class Identity:
    def __init__(self, key):
        self.key = key
        self.did = did_from_public(key.public_key().public_bytes_raw())

    @classmethod
    def load(cls, data_dir, create=False):
        folder = Path(data_dir) / 'identity'
        path = folder / 'ed25519.key'
        if folder.is_symlink() or folder.is_junction() or path.is_symlink():
            raise VeritasError('unsafe_identity_path')
        if not path.exists():
            if not create:
                raise VeritasError('identity_missing_run_init')
            folder.mkdir(parents=True, exist_ok=True, mode=0o700)
            if os.name == 'nt':
                protect_windows(folder)
            raw = Ed25519PrivateKey.generate().private_bytes_raw()
            try:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, 'wb') as f:
                    f.write(raw)
                    f.flush()
                    os.fsync(f.fileno())
            except FileExistsError:
                pass
        if os.name != 'nt' and path.stat().st_mode & 0o077:
            raise VeritasError('unsafe_private_key_permissions')
        if os.name == 'nt':
            protect_windows(folder)
            protect_windows(path)
        if path.stat().st_size != 32:
            raise VeritasError('identity_load_failed')
        try:
            return cls(Ed25519PrivateKey.from_private_bytes(path.read_bytes()))
        except (ValueError, OSError) as exc:
            raise VeritasError('identity_load_failed') from exc
