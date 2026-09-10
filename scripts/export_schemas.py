"""Export public JSON schemas without runtime keys or network access."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from veritas.security.sanitizer import Job
from veritas.attestation.schema import Attestation
from veritas.verification.semantic import Analysis

folder=Path(__file__).resolve().parents[1]/'docs'/'schemas'
folder.mkdir(parents=True,exist_ok=True)
for name,model in [('job',Job),('attestation',Attestation),('semantic-analysis',Analysis)]:
    schema=model.model_json_schema()
    schema['$schema']='https://json-schema.org/draft/2020-12/schema'
    (folder/f'{name}.schema.json').write_text(json.dumps(schema,indent=2)+'\n',encoding='utf-8')
