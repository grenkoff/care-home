# video

The Rust service of live video. It keeps the last seconds of every camera in memory as fragmented MP4 and answers `core` over gRPC ([`proto/video/v1`](../../proto/video/v1/video.proto)) with the HLS playlist, the init segment and a media segment of a stream. It owns no data and publishes no events: no database, no NATS, nothing on disk. Only `core` reaches it, inside the Docker network.

## Settings

| Variable | Default | Meaning |
|----------|---------|---------|
| `VIDEO_STREAMS` | `hall=demo` | the streams as `key=source` entries split by commas; the key is the stream key of a camera in the admin of `core`; the source is `demo` or the RTSP address of a camera, `rtsp://user:password@10.0.0.21:554/stream1` |
| `VIDEO_RTSP_TIMEOUT` | `10` | seconds a camera may stay silent before the service connects to it again |
| `VIDEO_GRPC_ADDR` | `0.0.0.0:50051` | gRPC for `core` |
| `VIDEO_HTTP_ADDR` | `0.0.0.0:8080` | the health check on `/health` |
| `RUST_LOG` | `info` | the level of the structured logs |

## Streams

- Every stream keeps its last 5 segments; a segment closes at the first key frame after 2 seconds, so it always starts with a key frame.
- The playlist calls the init segment `init.mp4` and a media segment `<number>.m4s`; `core` serves them next to the page of the camera.
- An unknown stream and a segment that already left the window give `NOT_FOUND`; a stream without a segment yet gives `UNAVAILABLE`.
- The init segment follows the latest parameter sets of the stream; a camera that changes its resolution while it runs is not handled yet.

## Cameras

- A camera sends its H.264 over RTP inside the RTSP connection (TCP), without re-encoding; the service takes the first H.264 video the camera describes, through the `retina` crate.
- Percent-encode every character of the user and the password but letters and digits (a comma as `%2C`, `@` as `%40`, `%` as `%25`): entries of `VIDEO_STREAMS` are split by commas. In `.env`, put the value in single quotes, so Compose does not read a `$` in it. The user and the password are hidden in the logs; a token in the query of the address is not, so give the camera its credentials as the user and the password.
- Addresses with passwords are secrets and never enter the repository: put `VIDEO_STREAMS` into `.env` at the root of the repository, which git ignores and Compose reads, or into the environment of the deployment. The logs name the stream and the host of the camera only.
- A camera that hangs up, sends no picture for longer than `VIDEO_RTSP_TIMEOUT` (RTCP reports do not count) or refuses the session is tried again after a pause that starts at 1 second and doubles up to 30 seconds; a session that brought pictures sets it back to 1 second. A camera that refuses the password or does not answer stops neither the service nor the other streams.
- After a lost session the stream starts a new window: `UNAVAILABLE` until its first segment, with segment numbers that keep growing, so a player never gets an old number with new pictures.
- Cameras send no B-frames: the RTP time of a picture must grow from one picture to the next, so a camera with B-frames (H.264 Main or High with B-frames on) loses its session at the first one; turn B-frames off in the camera.
- The service must reach the cameras: the network between the server and the home (a VPN) is outside the repository.

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
