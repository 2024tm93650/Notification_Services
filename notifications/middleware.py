"""Correlation ID middleware + log filter for distributed tracing."""
import logging
import uuid

CORRELATION_HEADER = 'HTTP_X_CORRELATION_ID'
_local_storage = {}


def get_correlation_id():
    import threading
    return _local_storage.get(threading.get_ident(), '-')


def set_correlation_id(cid):
    import threading
    _local_storage[threading.get_ident()] = cid


class CorrelationIdMiddleware:
    """Reads X-Correlation-ID from incoming request (or generates one) and
    echoes it back in the response. Other services should propagate this
    header to enable end-to-end request tracing across the system."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cid = request.META.get(CORRELATION_HEADER) or str(uuid.uuid4())
        request.correlation_id = cid
        set_correlation_id(cid)
        response = self.get_response(request)
        response['X-Correlation-ID'] = cid
        return response


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True
