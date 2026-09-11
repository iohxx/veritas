def extract_claims(job):
    # Preserve the complete submitted claim: semantic analysis covers every clause.
    return [{'claim_id':'claim_1', 'text':job.claim}]
