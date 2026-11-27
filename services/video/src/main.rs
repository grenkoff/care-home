//! Entry point of the video service.

use std::sync::Arc;
use std::time::Duration;

use contracts::video::v1::video_service_server::VideoServiceServer;
use tokio::signal::unix::SignalKind;
use tokio::task::JoinSet;
use video::api::endpoint::Endpoint;
use video::api::health::{Alive, Served};
use video::domain::frames::Framed;
use video::domain::mp4::TIMESCALE;
use video::domain::pause::Pause;
use video::infra::demo::{PATTERN_RATE, Pattern};
use video::infra::lineup::{Lineup, Wired};
use video::infra::listing::{Configured, Listing};
use video::infra::sources::Playing;

/// Segments every stream keeps in memory.
const SEGMENTS: usize = 5;

/// Seconds a segment reaches before the next key frame closes it.
const SEGMENT_SECONDS: u32 = 2;

/// Pause before connecting again to a camera that was lost after it sent pictures.
const FIRST_PAUSE: Duration = Duration::from_secs(1);

/// Longest pause between two attempts to reach a camera.
const LONGEST_PAUSE: Duration = Duration::from_secs(30);

/// Composition root: wires the streams, their sources, gRPC and the health check.
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let setting =
        |name: &str, fallback: &str| std::env::var(name).unwrap_or_else(|_| fallback.to_owned());
    let filter = tracing_subscriber::EnvFilter::new(setting("RUST_LOG", "info"));
    tracing_subscriber::fmt()
        .json()
        .with_env_filter(filter)
        .init();
    let grpc = setting("VIDEO_GRPC_ADDR", "0.0.0.0:50051").parse()?;
    let http = tokio::net::TcpListener::bind(setting("VIDEO_HTTP_ADDR", "0.0.0.0:8080")).await?;
    let silence = Duration::from_secs(setting("VIDEO_RTSP_TIMEOUT", "10").parse()?);
    let lineup = Lineup::new(
        Listing::new(setting("VIDEO_STREAMS", "hall=demo")).streams()?,
        (SEGMENTS, SEGMENT_SECONDS * TIMESCALE),
        (Pattern.frames().into(), PATTERN_RATE),
        (silence, Pause::new(FIRST_PAUSE, LONGEST_PAUSE)),
    );
    let streams = Arc::new(lineup.streams());
    let mut sources: JoinSet<_> = lineup
        .sources(&streams)
        .into_iter()
        .map(|source| async move { source.play().await })
        .collect();
    let mut terminated = tokio::signal::unix::signal(SignalKind::terminate())?;
    tracing::info!(%grpc, sources = sources.len(), "video is starting");
    let endpoint = VideoServiceServer::new(Endpoint::new(Arc::clone(&streams)));
    tokio::select! {
        served = tonic::transport::Server::builder().add_service(endpoint).serve(grpc) => served?,
        served = axum::serve(http, Alive.router()).into_future() => served?,
        Some(played) = sources.join_next() => played??,
        Ok(()) = tokio::signal::ctrl_c() => tracing::info!("video is stopping on an interrupt"),
        Some(()) = terminated.recv() => tracing::info!("video is stopping on termination"),
    }
    Ok(())
}
