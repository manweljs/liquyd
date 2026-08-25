# Liquyd

Liquyd is a lightweight async document and query toolkit with an ORM-like API.

## Aggregations

Liquyd wraps engine aggregations without applying application-specific limits or
time-range policies. Applications remain responsible for defining their own query
boundaries.

```python
from liquyd import Avg, Count, DateHistogram, Percentile, Terms

result = await RequestLog.filter(
    created_at__gte=date_from,
    created_at__lte=date_to,
).aggregate(
    total=Count(),
    errors=Count(status="error"),
    average_duration=Avg("duration_ms"),
    p95_duration=Percentile("duration_ms", 95),
    request_types=Terms(
        "request_type",
        aggregations={"average_duration": Avg("duration_ms")},
    ),
    trend=DateHistogram(
        "created_at",
        fixed_interval="5m",
        aggregations={"errors": Count(status="error")},
    ),
)
```

Available aggregation primitives:

- Metrics: `Avg`, `Min`, `Max`, `Sum`, `ValueCount`, `Cardinality`, and
  `Percentile`.
- Buckets: `Count`, `Filter`, `Terms`, and `DateHistogram`.
- Documents: `TopHits`.

Query filters support exact matching and the `in`, `gt`, `gte`, `lt`, and `lte`
lookups.
