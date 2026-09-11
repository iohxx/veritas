import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from veritas.errors import VeritasError

DEFAULT_WEIGHTS = {'accessibility':15, 'support':30, 'numerical':25, 'analysis':20, 'contradictions':10}


@dataclass
class Config:
    data_dir: Path = Path('data')
    room: str = 'veritas'
    technocore_url: str = 'https://technocore.chat'
    max_jobs_per_hour: int = 20
    max_posts_per_hour: int = 20
    max_inference_per_job: int = 1
    max_source_size: int = 1048576
    max_job_size: int = 65536
    request_timeout: int = 15
    inference_provider: str = 'none'
    inference_url: str = 'http://127.0.0.1:11434/api/chat'
    model: str = 'qwen3:4b'
    weights: dict = field(default_factory=lambda: DEFAULT_WEIGHTS.copy())

    @classmethod
    def from_env(cls):
        c = cls()
        for name in cls.__dataclass_fields__:
            value = os.environ.get('VERITAS_' + name.upper())
            if value is None or name == 'weights':
                continue
            try:
                old = getattr(c, name)
                setattr(c, name, int(value) if type(old) is int else Path(value) if isinstance(old, Path) else value)
            except ValueError as exc:
                raise VeritasError('invalid_configuration') from exc
        try:
            c.weights = json.loads(os.environ.get('VERITAS_CONFIDENCE_WEIGHTS', json.dumps(DEFAULT_WEIGHTS)))
            if set(c.weights) != set(DEFAULT_WEIGHTS) or any(type(v) is not int or v < 0 for v in c.weights.values()) or sum(c.weights.values()) != 100:
                raise ValueError()
            for name in cls.__dataclass_fields__:
                value = getattr(c, name)
                if type(value) is int and (value < (0 if name == 'max_inference_per_job' else 1) or value > 10000000):
                    raise ValueError()
            if c.request_timeout > 120:
                raise ValueError()
        except (ValueError, TypeError) as exc:
            raise VeritasError('invalid_configuration') from exc
        return c
