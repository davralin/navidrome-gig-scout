# 0009. Throttle Ticketmaster Requests Below Provider Limit

Date: 2026-09-02

## Status

Accepted

## Context

Ticketmaster documents a Discovery API rate limit of five requests per second.

Running at the documented ceiling leaves no operational margin for provider-side rate-window
implementation details, scheduler jitter, request timing variance, network latency, or retries.

This application runs as scheduled batch work and is not latency-sensitive. Predictable completion is
more important than maximizing request throughput.

## Decision

Throttle Ticketmaster Discovery API requests to one request per second by default.

This is intentionally below the documented provider limit and treats that limit as a ceiling, not a
target operating rate.

## Consequences

The default request pace has more headroom against `429 Too Many Requests` responses.

Full runs take longer in proportion to the number of artists queried.

The simpler fixed-rate throttle remains easy to understand and operate. Adaptive retry or backoff can
be added later if the fixed safer default is not enough.
