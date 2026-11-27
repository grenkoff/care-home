//! Units of an H.264 stream in the Annex B byte format.

/// Start code that comes before every unit of the stream.
const START: [u8; 3] = [0, 0, 1];

/// Kind of a NAL unit that the service tells apart.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Kind {
    /// Slice of a picture that refers to earlier pictures.
    Slice,
    /// Slice of a picture that starts a new group, a key frame.
    Key,
    /// Sequence parameter set.
    Sequence,
    /// Picture parameter set.
    Picture,
    /// Any other unit, such as a delimiter or supplemental information.
    Other,
}

/// NAL unit without its start code.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Unit {
    /// Bytes of the unit, its header first.
    bytes: Vec<u8>,
}

impl Unit {
    /// Creates a unit from its bytes, its header first.
    #[must_use]
    pub const fn new(bytes: Vec<u8>) -> Self {
        Self { bytes }
    }
}

/// Parts of a NAL unit.
pub trait Nal {
    /// Returns the kind of the unit, read from its header.
    fn kind(&self) -> Kind;
    /// Returns the bytes of the unit, its header first.
    fn bytes(&self) -> &[u8];
    /// Tells whether the unit is a slice that opens a picture.
    fn opening(&self) -> bool;
}

impl Nal for Unit {
    fn kind(&self) -> Kind {
        match self.bytes.first().map(|header| header & 0x1F) {
            Some(1) => Kind::Slice,
            Some(5) => Kind::Key,
            Some(7) => Kind::Sequence,
            Some(8) => Kind::Picture,
            _ => Kind::Other,
        }
    }

    fn bytes(&self) -> &[u8] {
        &self.bytes
    }

    fn opening(&self) -> bool {
        false
    }
}

/// Source of NAL units.
pub trait Units {
    /// Returns the units in the order of the stream.
    fn units(&self) -> Vec<Unit>;
}

/// Stream in the Annex B byte format: units after start codes.
#[derive(Debug, Clone, Copy)]
pub struct AnnexB<'a> {
    /// Bytes of the stream.
    bytes: &'a [u8],
}

impl<'a> AnnexB<'a> {
    /// Wraps the bytes of a stream.
    #[must_use]
    pub const fn new(bytes: &'a [u8]) -> Self {
        Self { bytes }
    }
}

impl Units for AnnexB<'_> {
    fn units(&self) -> Vec<Unit> {
        let starts: Vec<usize> = self
            .bytes
            .windows(START.len())
            .enumerate()
            .filter(|(_, window)| *window == START)
            .map(|(position, _)| position + START.len())
            .collect();
        let ends = starts
            .iter()
            .skip(1)
            .map(|start| start - START.len())
            .chain([self.bytes.len()]);
        starts
            .iter()
            .zip(ends)
            .map(|(&start, end)| &self.bytes[start..end])
            .map(|unit| {
                &unit[..unit
                    .iter()
                    .rposition(|byte| *byte != 0)
                    .map_or(0, |last| last + 1)]
            })
            .filter(|unit| !unit.is_empty())
            .map(|unit| Unit::new(unit.to_vec()))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::{AnnexB, Kind, Nal, Unit, Units};

    #[test]
    fn splits_the_stream_at_both_start_codes() {
        let stream = [
            0, 0, 0, 1, 0x67, 0x42, 0, 0, 0, 1, 0x68, 0xCE, 0, 0, 1, 0x65, 0x88, 0,
        ];
        assert_eq!(
            AnnexB::new(&stream).units(),
            [
                Unit::new(vec![0x67, 0x42]),
                Unit::new(vec![0x68, 0xCE]),
                Unit::new(vec![0x65, 0x88]),
            ]
        );
    }

    #[test]
    fn finds_no_units_without_a_start_code() {
        assert_eq!(AnnexB::new(&[0x65, 0x88, 0x84]).units(), []);
    }

    #[test]
    fn tells_the_kinds_of_units_apart() {
        let kinds: Vec<Kind> = [0x67, 0x68, 0x65, 0x41, 0x09]
            .into_iter()
            .map(|header| Unit::new(vec![header, 0x80]).kind())
            .collect();
        assert_eq!(
            kinds,
            [
                Kind::Sequence,
                Kind::Picture,
                Kind::Key,
                Kind::Slice,
                Kind::Other
            ]
        );
    }

    #[test]
    fn tells_a_slice_that_opens_a_picture() {
        let opening: Vec<bool> = [
            vec![0x41, 0x9A],
            vec![0x65, 0x88],
            vec![0x41, 0x1A],
            vec![0x67, 0x9A],
            vec![0x41],
        ]
        .into_iter()
        .map(|bytes| Unit::new(bytes).opening())
        .collect();
        assert_eq!(opening, [true, true, false, false, false]);
    }

    #[test]
    fn keeps_the_bytes_of_a_unit() {
        assert_eq!(Unit::new(vec![0x65, 0x88]).bytes(), [0x65, 0x88]);
    }
}
