from veritas.verification.sources import now

STATUSES = ('VERIFIED','PARTIALLY_VERIFIED','UNVERIFIED','CONTRADICTED','INSUFFICIENT_EVIDENCE')


def decide(job, numerical, semantic, contradictions, sources, weights, did):
    checks = numerical['checks']
    failed = any(c['outcome']=='fail' for c in checks)
    passed = bool(checks) and all(c['outcome']=='pass' for c in checks)
    findings = semantic.get('findings',[])
    direct = any(f['relation']=='direct' for f in findings)
    support = any(f['relation'] in ('direct','indirect') for f in findings)
    reasons = []
    if failed or contradictions['semantic_contradictions']:
        status = 'CONTRADICTED'
        reasons.append('calculation_mismatch' if failed else 'evidence_contradicts_claim')
    elif contradictions['conflicts']:
        status = 'INSUFFICIENT_EVIDENCE'
        reasons.append('conflicting_values_need_matching_context')
    elif numerical['pure_arithmetic'] and passed:
        status = 'VERIFIED'
        reasons.append('complete_arithmetic_claim_reproduced')
    elif not any(s.get('usable') and s.get('text') for s in sources):
        status = 'INSUFFICIENT_EVIDENCE'
        reasons.append('no_usable_evidence')
    elif not semantic.get('performed'):
        status = 'INSUFFICIENT_EVIDENCE'
        reasons.append(semantic.get('reason','semantic_analysis_missing'))
    elif semantic.get('full_claim_supported') and direct and (not checks or passed):
        status = 'VERIFIED'
        reasons.append('complete_claim_supported_with_citations')
    elif support:
        status = 'PARTIALLY_VERIFIED'
        reasons.append('only_partial_or_indirect_support')
    elif any(f['relation']=='insufficient' for f in findings):
        status = 'INSUFFICIENT_EVIDENCE'
        reasons.append('evidence_insufficient')
    else:
        status = 'UNVERIFIED'
        reasons.append('analysis_cannot_establish_claim')
    # Verification strength, integer 0..100. N/A checks excluded from denominator.
    components = {'accessibility':sum(bool(s['accessible']) for s in sources)*100//len(sources) if sources else None,
                  'support':100 if semantic.get('full_claim_supported') and direct else 50 if support else 0 if sources else None,
                  'numerical':100 if checks and all(c['outcome'] in ('pass','fail') for c in checks) else 0 if checks else None,
                  'analysis':100 if semantic.get('performed') else 0 if sources else None,
                  'contradictions':100 if contradictions['performed'] and not contradictions['conflicts'] and not contradictions['semantic_contradictions'] else 0 if sources else None}
    denominator = sum(weights[k] for k,v in components.items() if v is not None)
    confidence = sum(weights[k]*v for k,v in components.items() if v is not None)//denominator if denominator else 0
    return {'type':'VERITAS_VERDICT','version':'1.0','job_id':job.job_id,'status':status,'confidence':confidence,'confidence_scale':'0..100; verification strength, not probability of truth','components':components,'weights':weights,'reasons':reasons,'timestamp':now(),'verifier':did,'checks':checks,'evidence':[{'source_index':i,'sha256':s.get('sha256'),'accessible':s['accessible']} for i,s in enumerate(sources)]}
