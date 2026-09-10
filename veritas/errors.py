class VeritasError(Exception):
    """Safe, controlled public error."""


class NetworkError(VeritasError):
    def __init__(self, status=0):
        self.status = status
        super().__init__(f"network_failure:{status}")
