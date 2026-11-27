//! Streams of the setting, each with a window and a source.

use std::collections::BTreeMap;
use std::sync::{Arc, RwLock};

use crate::domain::frames::Frame;
use crate::domain::streams::Streams;
use crate::domain::window::Window;
use crate::infra::demo::Demo;
use crate::infra::listing::Source;

/// Streams of the service and the sources that fill them.
pub trait Wired {
    /// Returns the streams, each with an empty window.
    fn streams(&self) -> Streams;
    /// Returns a source for every stream, each filling the given streams.
    fn sources<R>(&self, streams: &Arc<R>) -> Vec<Demo<R>>;
}

/// Streams of the setting with the shape of their windows and the demo pictures.
#[derive(Debug, Clone)]
pub struct Lineup {
    /// Streams with their sources, as the setting lists them.
    listed: Vec<(String, Source)>,
    /// Shape of every window: segments it keeps and their target duration in ticks.
    shape: (usize, u32),
    /// Pictures of the demo and their rate.
    pattern: (Arc<[Frame]>, u32),
}

impl Lineup {
    /// Creates the lineup of the listed streams.
    #[must_use]
    pub const fn new(
        listed: Vec<(String, Source)>,
        shape: (usize, u32),
        pattern: (Arc<[Frame]>, u32),
    ) -> Self {
        Self {
            listed,
            shape,
            pattern,
        }
    }
}

impl Wired for Lineup {
    fn streams(&self) -> Streams {
        let (segments, target) = self.shape;
        Streams::new(
            self.listed
                .iter()
                .map(|(key, _)| (key.clone(), RwLock::new(Window::new(segments, target))))
                .collect::<BTreeMap<_, _>>(),
        )
    }

    fn sources<R>(&self, streams: &Arc<R>) -> Vec<Demo<R>> {
        let (frames, rate) = &self.pattern;
        self.listed
            .iter()
            .map(|(key, source)| match source {
                Source::Demo => {
                    Demo::new(key.clone(), Arc::clone(frames), *rate, Arc::clone(streams))
                }
            })
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use std::sync::Arc;

    use tokio::sync::mpsc::{UnboundedSender, unbounded_channel};

    use super::{Lineup, Wired};
    use crate::domain::frames::Frame;
    use crate::domain::nal::Unit;
    use crate::domain::streams::{Recorded, Refusal, Unrecorded, Watched};
    use crate::domain::window::Missing;
    use crate::infra::demo::Playing;
    use crate::infra::listing::Source;

    struct Tape {
        sender: UnboundedSender<(String, u32)>,
    }

    impl Recorded for Tape {
        fn record(&self, stream: &str, _frame: &Frame, duration: u32) -> Result<(), Unrecorded> {
            self.sender
                .send((stream.to_owned(), duration))
                .map_err(|_| Unrecorded::Unknown(stream.to_owned()))
        }
    }

    fn lineup() -> Lineup {
        Lineup::new(
            vec![
                (String::from("hall"), Source::Demo),
                (String::from("garden"), Source::Demo),
            ],
            (5, 180_000),
            (
                Arc::from([Frame::new(vec![Unit::new(vec![0x65, 0x88])])]),
                15,
            ),
        )
    }

    #[test]
    fn gives_every_listed_stream_an_empty_window() {
        let streams = lineup().streams();
        assert_eq!(
            [
                streams.playlist("hall"),
                streams.playlist("garden"),
                streams.playlist("roof")
            ],
            [
                Err(Refusal::Missing(Missing::Empty)),
                Err(Refusal::Missing(Missing::Empty)),
                Err(Refusal::Unknown(String::from("roof"))),
            ]
        );
    }

    #[tokio::test(start_paused = true)]
    async fn gives_every_stream_a_source_of_the_pattern_at_its_rate() {
        let (sender, mut receiver) = unbounded_channel();
        let sources = lineup().sources(&Arc::new(Tape { sender }));
        let playing: Vec<_> = sources
            .into_iter()
            .map(|source| tokio::spawn(async move { source.play().await }))
            .collect();
        let mut taken = Vec::new();
        while taken.len() < 2
            && let Some(record) = receiver.recv().await
        {
            taken.push(record);
        }
        playing.iter().for_each(tokio::task::JoinHandle::abort);
        taken.sort();
        assert_eq!(
            taken,
            [(String::from("garden"), 6000), (String::from("hall"), 6000)]
        );
    }
}
