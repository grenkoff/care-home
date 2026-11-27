//! Health check of the video service over HTTP.

use axum::Router;
use axum::routing::get;

/// Path that Docker asks for the health of the service.
const PATH: &str = "/health";

/// HTTP side of the service.
pub trait Served {
    /// Returns the routes the service answers over HTTP.
    fn router(&self) -> Router;
}

/// Health check that answers while the service runs.
#[derive(Debug, Clone, Copy, Default)]
pub struct Alive;

impl Served for Alive {
    fn router(&self) -> Router {
        Router::new().route(PATH, get(|| async { "alive" }))
    }
}

#[cfg(test)]
mod tests {
    use axum::body::{Body, to_bytes};
    use axum::http::{Request, StatusCode};
    use tower::ServiceExt;

    use super::{Alive, PATH, Served};

    #[tokio::test]
    async fn answers_that_the_service_is_alive() {
        let answer = Alive
            .router()
            .oneshot(Request::get(PATH).body(Body::empty()).unwrap())
            .await
            .unwrap();
        let status = answer.status();
        let body = to_bytes(answer.into_body(), 16).await.unwrap();
        assert_eq!((status, &body[..]), (StatusCode::OK, &b"alive"[..]));
    }
}
