//! Window of the last segments of one stream, kept in memory only.

use std::sync::Arc;

use crate::domain::frames::{Frame, Picture};
use crate::domain::mp4::{Encoded, Fragment, Sample, TIMESCALE, Track};
use crate::domain::sps::Unreadable;

/// Name of the init segment in the playlist.
pub const INIT: &str = "init.mp4";

/// Extension of the names of the media segments in the playlist.
pub const MEDIA: &str = "m4s";

/// Why the window cannot give what was asked.
#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
pub enum Missing {
    /// The stream has no segment yet.
    #[error("the stream has no segment yet")]
    Empty,
    /// The segment is not in the window: it left it or never came.
    #[error("the segment {0} is not in the window")]
    Gone(u32),
}

/// Segment of the window: its number, its duration and its bytes.
#[derive(Debug, Clone, PartialEq, Eq)]
struct Segment {
    /// Number of the segment in the stream.
    sequence: u32,
    /// Duration in ticks of the media clock.
    duration: u32,
    /// Bytes of the media segment, shared by every copy of the window.
    bytes: Arc<[u8]>,
}

/// Last segments of one stream and the pictures of the next one.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Window {
    /// Most segments the window keeps.
    capacity: usize,
    /// Duration in ticks a segment reaches before the next key frame closes it.
    target: u32,
    /// Track the latest parameter sets describe.
    track: Option<Track>,
    /// Closed segments, the oldest first.
    segments: Vec<Segment>,
    /// Samples of the segment that is not closed yet.
    pending: Vec<Sample>,
    /// Duration of the pending samples in ticks.
    elapsed: u32,
    /// Time of the first pending sample in ticks.
    start: u64,
    /// Number of the pending segment.
    sequence: u32,
}

impl Window {
    /// Creates an empty window that keeps the given count of segments of the target duration.
    #[must_use]
    pub const fn new(capacity: usize, target: u32) -> Self {
        Self {
            capacity,
            target,
            track: None,
            segments: Vec::new(),
            pending: Vec::new(),
            elapsed: 0,
            start: 0,
            sequence: 0,
        }
    }
}

/// Stream that grows by pictures.
pub trait Growing: Sized {
    /// Returns the stream with the picture of the duration at its end.
    fn with(self, frame: &Frame, duration: u32) -> Result<Self, Unreadable>;
}

/// Stream that its source starts anew, after the camera came back.
pub trait Restarting {
    /// Returns an empty stream that goes on with the numbers and the time of this one.
    #[must_use]
    fn restarted(self) -> Self;
}

/// Live stream as an HLS player reads it.
pub trait Live {
    /// Returns the init segment of the stream.
    fn init(&self) -> Result<Vec<u8>, Missing>;
    /// Returns the media playlist of the segments in the window.
    fn playlist(&self) -> Result<String, Missing>;
    /// Returns the media segment with the number.
    fn segment(&self, sequence: u32) -> Result<Vec<u8>, Missing>;
}

impl Window {
    /// Returns the window with the picture added to the pending segment.
    fn extended(self, sample: Sample, duration: u32) -> Self {
        Self {
            pending: self.pending.into_iter().chain([sample]).collect(),
            elapsed: self.elapsed.saturating_add(duration),
            ..self
        }
    }

    /// Returns the window with the pending segment closed and the picture opening the next one.
    fn closed(self, sample: Sample, duration: u32) -> Self {
        let segment = Segment {
            sequence: self.sequence,
            duration: self.elapsed,
            bytes: Fragment::new(self.sequence, self.start, self.pending)
                .encoded()
                .into(),
        };
        let segments: Vec<Segment> = self.segments.into_iter().chain([segment]).collect();
        let surplus = segments.len().saturating_sub(self.capacity);
        Self {
            segments: segments.into_iter().skip(surplus).collect(),
            pending: vec![sample],
            elapsed: duration,
            start: self.start + u64::from(self.elapsed),
            sequence: self.sequence + 1,
            ..self
        }
    }
}

impl Growing for Window {
    fn with(self, frame: &Frame, duration: u32) -> Result<Self, Unreadable> {
        let track = frame.track()?.or(self.track);
        let window = Self { track, ..self };
        Ok(
            if window.track.is_none() || (window.pending.is_empty() && !frame.key()) {
                window
            } else if frame.key() && window.elapsed >= window.target {
                window.closed(frame.sample(duration), duration)
            } else {
                window.extended(frame.sample(duration), duration)
            },
        )
    }
}

impl Restarting for Window {
    fn restarted(self) -> Self {
        Self {
            start: self.start + u64::from(self.elapsed),
            sequence: self.sequence + 1,
            ..Self::new(self.capacity, self.target)
        }
    }
}

impl Live for Window {
    fn init(&self) -> Result<Vec<u8>, Missing> {
        self.track
            .as_ref()
            .map(Encoded::encoded)
            .ok_or(Missing::Empty)
    }

    fn playlist(&self) -> Result<String, Missing> {
        let first = self.segments.first().ok_or(Missing::Empty)?;
        let longest = self
            .segments
            .iter()
            .map(|segment| segment.duration)
            .max()
            .unwrap_or_default();
        let header = format!(
            "#EXTM3U\n#EXT-X-VERSION:7\n#EXT-X-TARGETDURATION:{}\n#EXT-X-MEDIA-SEQUENCE:{}\n\
             #EXT-X-MAP:URI=\"{INIT}\"\n",
            longest.div_ceil(TIMESCALE),
            first.sequence
        );
        Ok(self.segments.iter().fold(header, |playlist, segment| {
            let millis = u64::from(segment.duration) * 1000 / u64::from(TIMESCALE);
            format!(
                "{playlist}#EXTINF:{}.{:03},\n{}.{MEDIA}\n",
                millis / 1000,
                millis % 1000,
                segment.sequence
            )
        }))
    }

    fn segment(&self, sequence: u32) -> Result<Vec<u8>, Missing> {
        if self.segments.is_empty() {
            return Err(Missing::Empty);
        }
        self.segments
            .iter()
            .find(|segment| segment.sequence == sequence)
            .map(|segment| segment.bytes.to_vec())
            .ok_or(Missing::Gone(sequence))
    }
}

#[cfg(test)]
mod tests {
    use super::{Growing, Live, Missing, Restarting, Window};
    use crate::domain::frames::{Frame, Picture};
    use crate::domain::mp4::{Encoded, Fragment, Track};
    use crate::domain::nal::Unit;
    use crate::domain::sps::{Size, Unreadable};

    const SEQUENCE: [u8; 10] = [0x67, 0x42, 0xC0, 0x1E, 0xD9, 0x00, 0xA0, 0x2F, 0xF9, 0x70];

    const PICTURE: [u8; 2] = [0x68, 0xCB];

    fn first() -> Frame {
        Frame::new(vec![
            Unit::new(SEQUENCE.to_vec()),
            Unit::new(PICTURE.to_vec()),
            Unit::new(vec![0x65, 0x88, 0x01]),
        ])
    }

    fn key() -> Frame {
        Frame::new(vec![Unit::new(vec![0x65, 0x88, 0x02])])
    }

    fn slice() -> Frame {
        Frame::new(vec![Unit::new(vec![0x41, 0x9A, 0x03])])
    }

    fn grown(capacity: usize, frames: &[Frame]) -> Window {
        frames
            .iter()
            .try_fold(Window::new(capacity, 12_000), |window, frame| {
                window.with(frame, 6000)
            })
            .unwrap()
    }

    fn fragment(sequence: u32, start: u64, frames: &[Frame]) -> Vec<u8> {
        Fragment::new(
            sequence,
            start,
            frames.iter().map(|frame| frame.sample(6000)).collect(),
        )
        .encoded()
    }

    #[test]
    fn starts_a_new_window_that_keeps_counting_segments() {
        let restarted = grown(3, &[first(), slice(), key(), slice(), key()]).restarted();
        let empty = (restarted.init(), restarted.playlist(), restarted.segment(1));
        let grown = [first(), slice(), key()]
            .iter()
            .try_fold(restarted, |window, frame| window.with(frame, 6000));
        assert_eq!(
            (
                empty,
                grown.map(|window| [window.segment(1), window.segment(3)])
            ),
            (
                (
                    Err(Missing::Empty),
                    Err(Missing::Empty),
                    Err(Missing::Empty)
                ),
                Ok([
                    Err(Missing::Gone(1)),
                    Ok(fragment(3, 30_000, &[first(), slice()]))
                ])
            )
        );
    }

    #[test]
    fn waits_for_the_parameter_sets_and_a_key_frame() {
        let window = grown(3, &[slice(), key(), slice(), key()]);
        assert_eq!(
            (window.init(), window.playlist(), window.segment(0)),
            (
                Err(Missing::Empty),
                Err(Missing::Empty),
                Err(Missing::Empty)
            )
        );
    }

    #[test]
    fn cuts_a_segment_at_the_first_key_frame_after_the_target_duration() {
        let window = grown(3, &[first(), slice(), key(), slice(), slice(), key()]);
        assert_eq!(
            [window.segment(0), window.segment(1)],
            [
                Ok(fragment(0, 0, &[first(), slice()])),
                Ok(fragment(1, 12_000, &[key(), slice(), slice()])),
            ]
        );
    }

    #[test]
    fn keeps_only_the_last_segments() {
        let window = grown(
            2,
            &[first(), slice(), key(), slice(), key(), slice(), key()],
        );
        assert_eq!(
            [window.segment(0), window.segment(1), window.segment(2)],
            [
                Err(Missing::Gone(0)),
                Ok(fragment(1, 12_000, &[key(), slice()])),
                Ok(fragment(2, 24_000, &[key(), slice()])),
            ]
        );
    }

    #[test]
    fn lists_the_segments_of_the_window_in_the_playlist() {
        let window = grown(
            2,
            &[
                first(),
                slice(),
                key(),
                slice(),
                key(),
                slice(),
                slice(),
                key(),
            ],
        );
        assert_eq!(
            window.playlist(),
            Ok(String::from(
                "#EXTM3U\n\
                 #EXT-X-VERSION:7\n\
                 #EXT-X-TARGETDURATION:1\n\
                 #EXT-X-MEDIA-SEQUENCE:1\n\
                 #EXT-X-MAP:URI=\"init.mp4\"\n\
                 #EXTINF:0.133,\n\
                 1.m4s\n\
                 #EXTINF:0.200,\n\
                 2.m4s\n"
            ))
        );
    }

    #[test]
    fn rounds_the_target_duration_up_to_whole_seconds() {
        let window = [first(), slice(), key()]
            .iter()
            .try_fold(Window::new(2, 90_000), |window, frame| {
                window.with(frame, 63_000)
            })
            .unwrap();
        assert_eq!(
            window.playlist().map(|playlist| {
                [
                    playlist.contains("#EXT-X-TARGETDURATION:2\n#EXT-X-MEDIA-SEQUENCE:0\n"),
                    playlist.contains("#EXTINF:1.400,\n0.m4s\n"),
                ]
            }),
            Ok([true, true])
        );
    }

    #[test]
    fn serves_the_init_segment_of_the_track() {
        let window = grown(2, &[first(), slice(), key()]);
        assert_eq!(
            window.init(),
            Ok(Track::new(Size::new(640, 360), SEQUENCE.to_vec(), PICTURE.to_vec()).encoded())
        );
    }

    #[test]
    fn refuses_a_segment_it_never_had() {
        let window = grown(2, &[first(), slice(), key()]);
        assert_eq!(window.segment(9), Err(Missing::Gone(9)));
    }

    #[test]
    fn refuses_a_picture_with_a_broken_parameter_set() {
        let broken = Frame::new(vec![
            Unit::new(vec![0x67, 0x42]),
            Unit::new(PICTURE.to_vec()),
            Unit::new(vec![0x65, 0x88]),
        ]);
        assert_eq!(
            Window::new(2, 12_000).with(&broken, 6000),
            Err(Unreadable::Short)
        );
    }
}
