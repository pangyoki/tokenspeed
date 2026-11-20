# EPD encode metrics

EPD encode mode runs a TokenSpeed encode loop instead of the language-model
scheduler. The loop owns admissions, cache decisions, batching, ring-slot
leases and copy completion; the EPD sender owns physical writes to prefill
ranks. Those owners emit through the same ts-metrics Metric exporter,
bounded relay and selected reporter as ordinary engine metrics.

The attention-TP group's first rank reports logical requests, image items,
queues, cache decisions, batching and copy-complete outcomes. Every encode TP
rank reports its physical writes with a tp_rank label. A write timeout is
counted as a transfer failure. Vision and ring-copy failures belong to the
logical failed-item counter and do not increment transfer failures.

ImageCount counts image items in a decoded encode request. The token offset
ranges within one image are not separate images. Encode wire requests usually
carry one item; an original HTTP request with multiple images can create
multiple encode items.

Queue snapshots refresh on state changes and at most once per second while
unchanged. Oldest age reads each FIFO queue head. Execution timing covers
data-plane submission through the already-existing device-copy completion
event; it includes forward-thread queueing and is not a synchronized GPU-only
measurement. Transfer timing covers the successful room-write worker and
excludes the wait for the full peer fanout.

Model-specific caches can expose scalar counters and gauges through the
optional EncoderSpec.cache_stats callback. The encode data plane samples this
callback on its forward thread and reports deltas through MetricFactory.
Missing callbacks add no samples. Snapshot errors warn once and do not stop
encoding. These values describe the reporting owner, not a cluster-wide cache
total; source-image and shared-preprocessing cache statistics remain separate.

Metric names and CAT scaling belong to the selected reporter plugin. The
matching ts-plugin metrics package maps tokenspeed:encoder events to existing
EncoderMetrics CAT names and report windows. A completed local SDK call is not
confirmation of backend receipt.
