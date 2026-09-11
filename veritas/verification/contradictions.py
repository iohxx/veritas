import re


def search(sources, semantic):
    conflicts = []
    # A conservative independent detector: identical metric labels, different values.
    # Context-free conflicts force INSUFFICIENT_EVIDENCE, never assert falsehood.
    values = {}
    pattern = re.compile(r'(?im)^\s*([A-Za-z][A-Za-z ]{0,40})\s*=\s*(\$?\d+(?:\.\d+)?\s*[BMK]?)\s*$')
    for i, source in enumerate(sources):
        for m in pattern.finditer(source.get('text','')):
            key = m[1].strip().lower()
            value = m[2].strip()
            if key in values and values[key][0] != value:
                conflicts.append({'kind':'ambiguous_metric_conflict','source_indices':[values[key][1],i],'metric':key,'values':[values[key][0],value]})
            else:
                values[key] = (value,i)
    direct = [f for f in semantic.get('findings',[]) if f['relation']=='contradicts']
    return {'performed':bool(any(s.get('usable') for s in sources)), 'scope':'submitted_sources_only', 'conflicts':conflicts, 'semantic_contradictions':direct}
