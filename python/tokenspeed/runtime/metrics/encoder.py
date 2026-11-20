# Copyright (c) 2026 LightSeek Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from tokenspeed.runtime.metrics.events import MetricEventSink
from tokenspeed.runtime.metrics.reporter import MetricFactory

COUNTERS = {
    "hits": "hits",
    "misses": "misses",
    "skipped": "skipped",
    "evictions": "evictions",
    "code_cache_hits": "code_hits",
    "bridge_cache_hits": "bridge_hits",
    "vision_computations": "vision_computations",
    "bridge_computations": "bridge_computations",
    "encoder_images": "images",
}
GAUGES = {
    "capacity_bytes": "capacity_bytes",
    "current_bytes": "current_bytes",
    "entries": "entries",
    "retiring_bytes": "retiring_bytes",
    "allocated_bytes": "allocated_bytes",
    "generation": "generation",
}


class EncoderCacheMetrics:
    """Export owner-thread model cache snapshots through MetricFactory."""

    def __init__(
        self,
        labels: dict[str, str],
        *,
        enabled: bool,
        reporters: list[str],
        event_sink: MetricEventSink | None = None,
        registry=None,
    ) -> None:
        factory = MetricFactory(
            enabled=enabled,
            reporters=reporters,
            event_sink=event_sink,
            registry=registry,
        )
        self._last: dict[str, int] | None = None
        self._counters = {
            field: factory.counter(
                name=f"tokenspeed:encoder_model_cache_{name}",
                documentation=f"Model encoder cache lifetime {field} increments.",
                labelnames=list(labels),
            ).labels(**labels)
            for field, name in COUNTERS.items()
        }
        self._gauges = {
            field: factory.gauge(
                name=f"tokenspeed:encoder_model_cache_{name}",
                documentation=f"Model encoder cache {field} snapshot.",
                labelnames=list(labels),
                multiprocess_mode="livemax",
            ).labels(**labels)
            for field, name in GAUGES.items()
        }

    def record(self, snapshot: dict[str, int]) -> None:
        for field in COUNTERS.keys() | GAUGES.keys():
            if field in snapshot and (
                type(snapshot[field]) is not int or snapshot[field] < 0
            ):
                raise ValueError(f"Invalid encoder cache snapshot field {field}")
        for field, metric in self._gauges.items():
            if field in snapshot:
                metric.set(snapshot[field])
        if self._last is not None:
            for field, metric in self._counters.items():
                if field in snapshot and field in self._last:
                    delta = snapshot[field] - self._last[field]
                    if delta > 0:
                        metric.inc(delta)
        self._last = dict(snapshot)
