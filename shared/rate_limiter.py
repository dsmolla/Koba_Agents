from ratelimit import limits, RateLimitException
from backoff import on_exception, expo

ONE_MINUTE = 60

@on_exception(expo, RateLimitException, max_tries=5)
@limits(calls=150, period=ONE_MINUTE)
def gmail_rate_limiter():
    """Empty function just to check for Gmail API rate limit"""
    return

