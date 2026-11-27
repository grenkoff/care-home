//! Entry point of the video service.

use std::sync::Arc;

use contracts::video::v1::video_service_server::VideoServiceServer;
use tokio::task::JoinSet;
use video::api::endpoint::Endpoint;
use video::api::health::{Alive, Served};
use video::domain::frames::Framed;
use video::domain::mp4::TIMESCALE;
use video::infra::demo::{PATTERN_RATE, Pattern, Playing};
use video::infra::lineup::{Lineup, Wired};
use video::infra::listing::{Configured, Listing};

/// Segments every stream keeps in memory.
const SEGMENTS: usize = 5;

/// Seconds a segment reaches before the next key frame closes it.
const SEGMENT_SECONDS: u32 = 2;

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
    let lineup = Lineup::new(
        Listing::new(setting("VIDEO_STREAMS", "hall=demo")).streams()?,
        (SEGMENTS, SEGMENT_SECONDS * TIMESCALE),
        (Pattern.frames().into(), PATTERN_RATE),
    );
    let streams = Arc::new(lineup.streams());
    let mut sources: JoinSet<_> = lineup
        .sources(&streams)
        .into_iter()
        .map(|source| async move { source.play().await })
        .collect();
    tracing::info!(%grpc, sources = sources.len(), "video is starting");
    let stop = || async {
        if let Err(error) = tokio::signal::ctrl_c().await {
            tracing::error!(%error, "cannot listen for the shutdown signal");
        }
    };
    let endpoint = VideoServiceServer::new(Endpoint::new(Arc::clone(&streams)));
    tokio::select! {
        served = tonic::transport::Server::builder()
            .add_service(endpoint)
            .serve_with_shutdown(grpc, stop()) => served?,
        served = axum::serve(http, Alive.router()).with_graceful_shutdown(stop()) => served?,
        Some(played) = sources.join_next() => played??,
    }
    Ok(())
}
