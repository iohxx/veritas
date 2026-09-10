def backoff(failures):
    return min(60,2**min(failures,6))
