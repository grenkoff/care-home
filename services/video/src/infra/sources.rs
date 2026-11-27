//! Sources that fill the streams with pictures.

use crate::domain::streams::Unrecorded;

/// Source that keeps putting pictures into a stream.
pub trait Playing {
    /// Plays into the stream until a picture finds no stream to go into, and returns why.
    fn play(&self) -> impl Future<Output = Result<(), Unrecorded>> + Send;
}
