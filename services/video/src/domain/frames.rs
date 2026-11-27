//! Pictures of a stream: the units of one access unit each.

use crate::domain::mp4::{Sample, Track};
use crate::domain::nal::Unit;
use crate::domain::sps::Unreadable;

/// Picture of a stream with every unit that belongs to it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Frame {
    /// Units of the picture in the order of the stream.
    units: Vec<Unit>,
}

impl Frame {
    /// Creates a picture from its units.
    #[must_use]
    pub const fn new(units: Vec<Unit>) -> Self {
        Self { units }
    }
}

/// Picture that goes into a track.
pub trait Picture {
    /// Tells whether the picture is a key frame.
    fn key(&self) -> bool;
    /// Returns the sample of the picture: its slices, each after its length.
    fn sample(&self, duration: u32) -> Sample;
    /// Returns the track the parameter sets of the picture describe, when it carries both.
    fn track(&self) -> Result<Option<Track>, Unreadable>;
}

impl Picture for Frame {
    fn key(&self) -> bool {
        self.units.is_empty()
    }

    fn sample(&self, duration: u32) -> Sample {
        Sample::new(Vec::new(), duration, self.units.is_empty())
    }

    fn track(&self) -> Result<Option<Track>, Unreadable> {
        Ok(None)
    }
}

/// Source of the pictures of a stream.
pub trait Framed {
    /// Returns the pictures in the order of the stream.
    fn frames(&self) -> Vec<Frame>;
}

/// Pictures made of the units of a stream in their order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Pictures {
    /// Units of the stream.
    units: Vec<Unit>,
}

impl Pictures {
    /// Wraps the units of a stream.
    #[must_use]
    pub const fn new(units: Vec<Unit>) -> Self {
        Self { units }
    }
}

impl Framed for Pictures {
    fn frames(&self) -> Vec<Frame> {
        vec![Frame::new(self.units.clone())]
    }
}

#[cfg(test)]
mod tests {
    use super::{Frame, Framed, Picture, Pictures};
    use crate::domain::mp4::{Sample, Track};
    use crate::domain::nal::Unit;
    use crate::domain::sps::{Size, Unreadable};

    fn units(bytes: &[&[u8]]) -> Vec<Unit> {
        bytes.iter().map(|unit| Unit::new(unit.to_vec())).collect()
    }

    const SEQUENCE: [u8; 10] = [0x67, 0x42, 0xC0, 0x1E, 0xD9, 0x00, 0xA0, 0x2F, 0xF9, 0x70];

    #[test]
    fn groups_units_into_pictures_at_their_first_slices() {
        let stream = units(&[
            &SEQUENCE,
            &[0x68, 0xCB],
            &[0x06, 0x05],
            &[0x65, 0x88],
            &[0x41, 0x9A],
            &[0x41, 0x9B],
        ]);
        assert_eq!(
            Pictures::new(stream).frames(),
            [
                Frame::new(units(&[
                    &SEQUENCE,
                    &[0x68, 0xCB],
                    &[0x06, 0x05],
                    &[0x65, 0x88]
                ])),
                Frame::new(units(&[&[0x41, 0x9A]])),
                Frame::new(units(&[&[0x41, 0x9B]])),
            ]
        );
    }

    #[test]
    fn keeps_further_slices_in_their_picture() {
        let stream = units(&[&[0x65, 0x88], &[0x65, 0x44], &[0x41, 0x9A]]);
        assert_eq!(
            Pictures::new(stream).frames(),
            [
                Frame::new(units(&[&[0x65, 0x88], &[0x65, 0x44]])),
                Frame::new(units(&[&[0x41, 0x9A]])),
            ]
        );
    }

    #[test]
    fn opens_a_picture_at_a_delimiter_after_slices() {
        let stream = units(&[&[0x41, 0x9A], &[0x09, 0xF0], &[0x41, 0x9A]]);
        assert_eq!(
            Pictures::new(stream).frames(),
            [
                Frame::new(units(&[&[0x41, 0x9A]])),
                Frame::new(units(&[&[0x09, 0xF0], &[0x41, 0x9A]])),
            ]
        );
    }

    #[test]
    fn tells_a_key_frame_from_others() {
        assert_eq!(
            [
                Frame::new(units(&[&[0x09, 0xF0], &[0x65, 0x88]])).key(),
                Frame::new(units(&[&[0x09, 0xF0], &[0x41, 0x9A]])).key(),
            ],
            [true, false]
        );
    }

    #[test]
    fn keeps_only_the_slices_in_the_sample() {
        let frame = Frame::new(units(&[
            &SEQUENCE,
            &[0x68, 0xCB],
            &[0x65, 0x88, 0x84],
            &[0x65, 0x44],
        ]));
        assert_eq!(
            frame.sample(6000),
            Sample::new(
                vec![0, 0, 0, 3, 0x65, 0x88, 0x84, 0, 0, 0, 2, 0x65, 0x44],
                6000,
                true
            )
        );
    }

    #[test]
    fn describes_the_track_by_its_parameter_sets() {
        let frame = Frame::new(units(&[&SEQUENCE, &[0x68, 0xCB], &[0x65, 0x88]]));
        assert_eq!(
            frame.track(),
            Ok(Some(Track::new(
                Size::new(640, 360),
                SEQUENCE.to_vec(),
                vec![0x68, 0xCB]
            )))
        );
    }

    #[test]
    fn describes_no_track_without_both_parameter_sets() {
        assert_eq!(
            [
                Frame::new(units(&[&SEQUENCE, &[0x65, 0x88]])).track(),
                Frame::new(units(&[&[0x68, 0xCB], &[0x65, 0x88]])).track(),
            ],
            [Ok(None), Ok(None)]
        );
    }

    #[test]
    fn refuses_a_broken_sequence_parameter_set() {
        let frame = Frame::new(units(&[&[0x67, 0x42], &[0x68, 0xCB], &[0x65, 0x88]]));
        assert_eq!(frame.track(), Err(Unreadable::Short));
    }
}
