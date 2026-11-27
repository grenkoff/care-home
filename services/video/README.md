# video

The Rust service of live video. It keeps the last seconds of every camera in memory as fragmented MP4 and answers `core` over gRPC ([`proto/video/v1`](../../proto/video/v1/video.proto)) with the HLS playlist, the init segment and a media segment of a stream. It owns no data and publishes no events: no database, no NATS, nothing on disk. Only `core` reaches it, inside the Docker network.

## Settings

| Variable | Default | Meaning |
|----------|---------|---------|
| `VIDEO_STREAMS` | `hall=demo` | the streams as `key=source` entries split by commas; the key is the stream key of a camera in the admin of `core`; the only source for now is `demo` |
| `VIDEO_GRPC_ADDR` | `0.0.0.0:50051` | gRPC for `core` |
| `VIDEO_HTTP_ADDR` | `0.0.0.0:8080` | the health check on `/health` |
| `RUST_LOG` | `info` | the level of the structured logs |

## Streams

- Every stream keeps its last 5 segments; a segment closes at the first key frame after 2 seconds, so it always starts with a key frame.
- The playlist calls the init segment `init.mp4` and a media segment `<number>.m4s`; `core` serves them next to the page of the camera.
- An unknown stream and a segment that already left the window give `NOT_FOUND`; a stream without a segment yet gives `UNAVAILABLE`.
- The init segment follows the latest parameter sets of the stream; a camera that changes its resolution while it runs is not handled yet.

## Demo pattern

`demo/pattern.h264` is 4 seconds of the ffmpeg test source `testsrc2` (no people): 640×360, 15 frames a second, H.264 Constrained Baseline, a key frame every second. It was built once with ffmpeg in Docker, so nothing is installed on the machine:

```bash
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/services/video/demo:/out" \
  jrottenberg/ffmpeg:7.1-ubuntu2404 -hide_banner -loglevel error -y \
  -f lavfi -i testsrc2=size=640x360:rate=15 -t 4 \
  -c:v libx264 -profile:v baseline -level 3.0 -pix_fmt yuv420p -crf 30 \
  -g 15 -keyint_min 15 -sc_threshold 0 -bf 0 -x264-params slices=1 \
  -f h264 /out/pattern.h264
```

A new pattern keeps the frame rate of `PATTERN_RATE` in `src/infra/demo.rs`.
