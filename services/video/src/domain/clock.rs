//! Durations of the pictures of a camera, told by the clock of its stream.

use crate::domain::frames::Frame;

/// Why a picture cannot be timed by the clock of the camera.
#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("the clock of the camera jumped from {0} to {1}")]
pub struct Jumped(i64, i64);

/// Pictures that learn their duration from the time of the next one.
pub trait Timed: Sized {
    /// Takes the picture at the time and releases the previous one with its duration.
    fn followed(self, time: i64, frame: Frame) -> Result<(Self, Option<(Frame, u32)>), Jumped>;
}

/// Picture held back with its time until the next one comes.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Held {
    /// Time of the held picture in ticks of the clock and the picture itself.
    picture: Option<(i64, Frame)>,
}

impl Held {
    /// Creates the clock before the first picture.
    #[must_use]
    pub const fn new() -> Self {
        Self { picture: None }
    }
}

impl Timed for Held {
    fn followed(self, time: i64, frame: Frame) -> Result<(Self, Option<(Frame, u32)>), Jumped> {
        Ok((
            Self {
                picture: Some((time, frame)),
            },
            None,
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::{Held, Jumped, Timed};
    use crate::domain::frames::Frame;
    use crate::domain::nal::Unit;

    fn picture(mark: u8) -> Frame {
        Frame::new(vec![Unit::new(vec![0x41, mark])])
    }

    fn released(times: &[i64]) -> Result<Vec<Option<(Frame, u32)>>, Jumped> {
        times
            .iter()
            .zip(0..)
            .try_fold(
                (Held::new(), Vec::new()),
                |(held, released), (time, mark)| {
                    let (held, frame) = held.followed(*time, picture(mark))?;
                    Ok((held, released.into_iter().chain([frame]).collect()))
                },
            )
            .map(|(_, released)| released)
    }

    #[test]
    fn times_a_picture_by_the_rtp_clock_of_the_next_one() {
        assert_eq!(
            released(&[-3_000, 3_000, 9_000, 15_001]),
            Ok(vec![
                None,
                Some((picture(0), 6_000)),
                Some((picture(1), 6_000)),
                Some((picture(2), 6_001)),
            ])
        );
    }

    #[test]
    fn refuses_a_clock_that_does_not_grow() {
        assert_eq!(
            [released(&[3_000, 3_000]), released(&[3_000, 2_999])],
            [Err(Jumped(3_000, 3_000)), Err(Jumped(3_000, 2_999))]
        );
    }

    #[test]
    fn refuses_a_gap_too_long_for_a_duration() {
        let longest = i64::from(u32::MAX);
        assert_eq!(
            [released(&[0, longest]), released(&[0, longest + 1])],
            [
                Ok(vec![None, Some((picture(0), u32::MAX))]),
                Err(Jumped(0, longest + 1))
            ]
        );
    }
}
