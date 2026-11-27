//! gRPC endpoint of the video service.

use std::sync::Arc;

use contracts::video::v1::video_service_server::VideoService;
use contracts::video::v1::{
    InitRequest, InitResponse, PlaylistRequest, PlaylistResponse, SegmentRequest, SegmentResponse,
};
use tonic::{Request, Response, Status};

use crate::domain::streams::Watched;

/// Adapter: answers the requests of core for the live streams over gRPC.
#[derive(Debug)]
pub struct Endpoint<S> {
    /// Streams the endpoint reads.
    streams: Arc<S>,
}

impl<S> Endpoint<S> {
    /// Creates the endpoint that reads the streams.
    #[must_use]
    pub const fn new(streams: Arc<S>) -> Self {
        Self { streams }
    }
}

#[tonic::async_trait]
impl<S: Watched + Send + Sync + 'static> VideoService for Endpoint<S> {
    async fn playlist(
        &self,
        request: Request<PlaylistRequest>,
    ) -> Result<Response<PlaylistResponse>, Status> {
        let _ = (request, &self.streams);
        Err(Status::internal("not yet"))
    }

    async fn init(&self, request: Request<InitRequest>) -> Result<Response<InitResponse>, Status> {
        let _ = request;
        Err(Status::internal("not yet"))
    }

    async fn segment(
        &self,
        request: Request<SegmentRequest>,
    ) -> Result<Response<SegmentResponse>, Status> {
        let _ = request;
        Err(Status::internal("not yet"))
    }
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;
    use std::sync::{Arc, RwLock};

    use contracts::video::v1::video_service_server::VideoService;
    use contracts::video::v1::{InitRequest, PlaylistRequest, SegmentRequest};
    use tonic::{Code, Request};

    use super::Endpoint;
    use crate::domain::frames::Frame;
    use crate::domain::nal::Unit;
    use crate::domain::streams::{Recorded, Streams, Watched};
    use crate::domain::window::Window;

    fn streams() -> Arc<Streams> {
        let streams = Arc::new(Streams::new(BTreeMap::from([
            (String::from("hall"), RwLock::new(Window::new(2, 12_000))),
            (String::from("garden"), RwLock::new(Window::new(2, 12_000))),
        ])));
        let frames = [
            Frame::new(vec![
                Unit::new(vec![
                    0x67, 0x42, 0xC0, 0x1E, 0xD9, 0x00, 0xA0, 0x2F, 0xF9, 0x70,
                ]),
                Unit::new(vec![0x68, 0xCB]),
                Unit::new(vec![0x65, 0x88, 0x01]),
            ]),
            Frame::new(vec![Unit::new(vec![0x41, 0x9A, 0x03])]),
            Frame::new(vec![Unit::new(vec![0x65, 0x88, 0x02])]),
        ];
        for frame in &frames {
            streams.record("hall", frame, 6000).unwrap();
        }
        streams
    }

    async fn codes(endpoint: &Endpoint<Streams>, stream: &str, sequence: u64) -> [Code; 3] {
        [
            endpoint
                .playlist(Request::new(PlaylistRequest {
                    stream: stream.to_owned(),
                }))
                .await
                .map_or_else(|status| status.code(), |_| Code::Ok),
            endpoint
                .init(Request::new(InitRequest {
                    stream: stream.to_owned(),
                }))
                .await
                .map_or_else(|status| status.code(), |_| Code::Ok),
            endpoint
                .segment(Request::new(SegmentRequest {
                    stream: stream.to_owned(),
                    sequence,
                }))
                .await
                .map_or_else(|status| status.code(), |_| Code::Ok),
        ]
    }

    #[tokio::test]
    async fn answers_the_playlist_the_init_and_a_segment_of_a_stream() {
        let streams = streams();
        let endpoint = Endpoint::new(Arc::clone(&streams));
        let answers = (
            endpoint
                .playlist(Request::new(PlaylistRequest {
                    stream: String::from("hall"),
                }))
                .await
                .map(|response| response.into_inner().playlist),
            endpoint
                .init(Request::new(InitRequest {
                    stream: String::from("hall"),
                }))
                .await
                .map(|response| response.into_inner().init),
            endpoint
                .segment(Request::new(SegmentRequest {
                    stream: String::from("hall"),
                    sequence: 0,
                }))
                .await
                .map(|response| response.into_inner().segment),
        );
        assert_eq!(
            (answers.0.ok(), answers.1.ok(), answers.2.ok()),
            (
                streams.playlist("hall").ok(),
                streams.init("hall").ok(),
                streams.segment("hall", 0).ok()
            )
        );
    }

    #[tokio::test]
    async fn answers_not_found_for_a_stream_it_does_not_have() {
        let endpoint = Endpoint::new(streams());
        assert_eq!(codes(&endpoint, "roof", 0).await, [Code::NotFound; 3]);
    }

    #[tokio::test]
    async fn answers_unavailable_while_a_stream_has_no_segment() {
        let endpoint = Endpoint::new(streams());
        assert_eq!(codes(&endpoint, "garden", 0).await, [Code::Unavailable; 3]);
    }

    #[tokio::test]
    async fn answers_not_found_for_a_segment_outside_the_window() {
        let endpoint = Endpoint::new(streams());
        assert_eq!(
            [
                codes(&endpoint, "hall", 7).await[2],
                codes(&endpoint, "hall", u64::from(u32::MAX) + 1).await[2],
            ],
            [Code::NotFound, Code::NotFound]
        );
    }
}
