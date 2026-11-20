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

"""Model cache snapshots use the same MetricFactory as engine metrics."""

from tokenspeed.runtime.metrics.encoder import EncoderCacheMetrics


class Sink:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)


def test_cache_snapshots_prime_counters_and_export_deltas_and_gauges():
    sink = Sink()
    metrics = EncoderCacheMetrics(
        {"model_name": "encoder", "app_key": "test.encoder", "dp_rank": "0"},
        enabled=True,
        reporters=["pycat"],
        event_sink=sink,
    )
    metrics.record({"hits": 8, "misses": 3, "current_bytes": 1024, "generation": 0})
    metrics.record({"hits": 10, "misses": 4, "current_bytes": 2048, "generation": 0})
    metrics.record({"hits": 10, "misses": 4, "current_bytes": 0, "generation": 1})
    assert [
        (event.metric, event.value) for event in sink.events if event.operation == "inc"
    ] == [
        ("tokenspeed:encoder_model_cache_hits_total", 2),
        ("tokenspeed:encoder_model_cache_misses_total", 1),
    ]
    assert [
        event.value
        for event in sink.events
        if event.metric == "tokenspeed:encoder_model_cache_current_bytes"
    ] == [1024, 2048, 0]
    assert all(
        event.labels
        == {
            "model_name": "encoder",
            "app_key": "test.encoder",
            "dp_rank": "0",
        }
        for event in sink.events
    )


def test_cache_snapshot_validation_does_not_advance_counter_baseline():
    sink = Sink()
    metrics = EncoderCacheMetrics(
        {"model_name": "encoder"}, enabled=True, reporters=["pycat"], event_sink=sink
    )
    metrics.record({"hits": 1})
    try:
        metrics.record({"hits": -1})
    except ValueError:
        pass
    else:
        raise AssertionError("negative lifetime counter must be rejected")
    metrics.record({"hits": 4})
    assert [
        (event.operation, event.value)
        for event in sink.events
        if event.metric == "tokenspeed:encoder_model_cache_hits_total"
    ] == [("inc", 3)]
