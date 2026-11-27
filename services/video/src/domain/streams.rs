//! Live streams of the cameras kept by their keys.

use std::collections::BTreeMap;
use std::sync::RwLock;

use crate::domain::frames::Frame;
use crate::domain::sps::Unreadable;
use crate::domain::window::{Missing, Window};

/// Why a stream cannot give what a viewer asked.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum Refusal {
    /// No stream has the key.
    #[error("there is no stream {0}")]
    Unknown(String),
    /// The stream has not got what was asked.
    #[error(transparent)]
    Missing(#[from] Missing),
}

/// Why a picture does not go into a stream.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum Unrecorded {
    /// No stream has the key.
    #[error("there is no stream {0}")]
    Unknown(String),
    /// The parameter sets of the picture cannot be read.
    #[error(transparent)]
    Unreadable(#[from] Unreadable),
}

/// Streams as their viewers read them.
pub trait Watched {
    /// Returns the init segment of the stream.
    fn init(&self, stream: &str) -> Result<Vec<u8>, Refusal>;
    /// Returns the media playlist of the stream.
    fn playlist(&self, stream: &str) -> Result<String, Refusal>;
    /// Returns the media segment of the stream with the number.
    fn segment(&self, stream: &str, sequence: u32) -> Result<Vec<u8>, Refusal>;
}

/// Streams as their sources fill them.
pub trait Recorded {
    /// Adds the picture of the duration at the end of the stream.
    fn record(&self, stream: &str, frame: &Frame, duration: u32) -> Result<(), Unrecorded>;
}

/// Windows of the streams by their keys, each behind its own lock.
#[derive(Debug)]
pub struct Streams {
    /// Window of every stream by its key.
    windows: BTreeMap<String, RwLock<Window>>,
}

impl Streams {
    /// Keeps the windows of the streams by their keys.
    #[must_use]
    pub const fn new(windows: BTreeMap<String, RwLock<Window>>) -> Self {
        Self { windows }
    }
}

impl Watched for Streams {
    fn init(&self, stream: &str) -> Result<Vec<u8>, Refusal> {
        Err(Refusal::Unknown(stream.to_owned()))
    }

    fn playlist(&self, stream: &str) -> Result<String, Refusal> {
        Err(Refusal::Unknown(stream.to_owned()))
    }

    fn segment(&self, stream: &str, sequence: u32) -> Result<Vec<u8>, Refusal> {
        Err(Refusal::Unknown(format!("{stream}{sequence}")))
    }
}

impl Recorded for Streams {
    fn record(&self, stream: &str, frame: &Frame, duration: u32) -> Result<(), Unrecorded> {
        let _ = (frame, duration, self.windows.len());
        Err(Unrecorded::Unknown(stream.to_owned()))
    }
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;
    use std::sync::RwLock;

    use super::{Recorded, Refusal, Streams, Unrecorded, Watched};
    use crate::domain::frames::{Frame, Picture};
    use crate::domain::mp4::{Encoded, Fragment};
    use crate::domain::nal::Unit;
    use crate::domain::sps::Unreadable;
    use crate::domain::window::{Growing, Live, Missing, Window};

    fn first() -> Frame {
        Frame::new(vec![
            Unit::new(vec![
                0x67, 0x42, 0xC0, 0x1E, 0xD9, 0x00, 0xA0, 0x2F, 0xF9, 0x70,
            ]),
            Unit::new(vec![0x68, 0xCB]),
            Unit::new(vec![0x65, 0x88, 0x01]),
        ])
    }

    fn key() -> Frame {
        Frame::new(vec![Unit::new(vec![0x65, 0x88, 0x02])])
    }

    fn slice() -> Frame {
        Frame::new(vec![Unit::new(vec![0x41, 0x9A, 0x03])])
    }

    fn streams() -> Streams {
        Streams::new(BTreeMap::from([
            (String::from("hall"), RwLock::new(Window::new(2, 12_000))),
            (String::from("garden"), RwLock::new(Window::new(2, 12_000))),
        ]))
    }

    fn recorded(frames: &[Frame]) -> Streams {
        let streams = streams();
        for frame in frames {
            assert_eq!(streams.record("hall", frame, 6000), Ok(()));
        }
        streams
    }

    fn expected(frames: &[Frame]) -> Window {
        frames
            .iter()
            .try_fold(Window::new(2, 12_000), |window, frame| {
                window.with(frame, 6000)
            })
            .unwrap()
    }

    #[test]
    fn serves_what_was_recorded_into_a_stream() {
        let frames = [first(), slice(), key()];
        let streams = recorded(&frames);
        assert_eq!(
            (
                streams.init("hall"),
                streams.playlist("hall"),
                streams.segment("hall", 0)
            ),
            (
                Ok(expected(&frames).init().unwrap()),
                Ok(expected(&frames).playlist().unwrap()),
                Ok(Fragment::new(0, 0, vec![first().sample(6000), slice().sample(6000)]).encoded())
            )
        );
    }

    #[test]
    fn keeps_every_stream_apart() {
        let streams = recorded(&[first(), slice(), key()]);
        assert_eq!(
            (
                streams.init("garden"),
                streams.playlist("garden"),
                streams.segment("garden", 0)
            ),
            (
                Err(Refusal::Missing(Missing::Empty)),
                Err(Refusal::Missing(Missing::Empty)),
                Err(Refusal::Missing(Missing::Empty))
            )
        );
    }

    #[test]
    fn refuses_a_stream_it_does_not_have() {
        let streams = recorded(&[first(), slice(), key()]);
        assert_eq!(
            (
                streams.init("roof"),
                streams.playlist("roof"),
                streams.segment("roof", 0),
                streams.record("roof", &first(), 6000)
            ),
            (
                Err(Refusal::Unknown(String::from("roof"))),
                Err(Refusal::Unknown(String::from("roof"))),
                Err(Refusal::Unknown(String::from("roof"))),
                Err(Unrecorded::Unknown(String::from("roof")))
            )
        );
    }

    #[test]
    fn keeps_the_stream_as_it_was_after_a_broken_picture() {
        let streams = recorded(&[first(), slice(), key()]);
        let broken = Frame::new(vec![
            Unit::new(vec![0x67, 0x42]),
            Unit::new(vec![0x68, 0xCB]),
            Unit::new(vec![0x65, 0x88]),
        ]);
        assert_eq!(
            (
                streams.record("hall", &broken, 6000),
                streams.playlist("hall")
            ),
            (
                Err(Unrecorded::Unreadable(Unreadable::Short)),
                Ok(expected(&[first(), slice(), key()]).playlist().unwrap())
            )
        );
    }
}
