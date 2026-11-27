FROM rust:1-slim-bookworm AS build

RUN apt-get update \
  && apt-get install --no-install-recommends -y protobuf-compiler \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY Cargo.toml Cargo.lock ./
COPY proto ./proto
COPY contracts ./contracts
COPY tools ./tools
COPY services/images ./services/images
COPY services/video ./services/video

RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
  --mount=type=cache,target=/src/target,sharing=locked \
  cargo build --release --locked -p video \
  && cp target/release/video /usr/local/bin/video


FROM debian:bookworm-slim AS runtime

RUN apt-get update \
  && apt-get install --no-install-recommends -y ca-certificates curl \
  && rm -rf /var/lib/apt/lists/* \
  && useradd --system --uid 1000 live

COPY --from=build /usr/local/bin/video /usr/local/bin/video

USER live
EXPOSE 50051 8080
HEALTHCHECK --interval=5s --timeout=3s --retries=10 \
  CMD curl -fsS http://localhost:8080/health || exit 1
ENTRYPOINT ["video"]
