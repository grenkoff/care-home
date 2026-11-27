//! Fragmented MP4 of one H.264 track: the init segment and the media segments.

use crate::domain::sps::{Sides, Size};

/// Bytes of a piece of a file.
pub trait Encoded {
    /// Returns the bytes of the piece.
    fn encoded(&self) -> Vec<u8>;
}

/// Track of H.264 pictures described by their size and parameter sets.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Track {
    /// Size of every picture.
    size: Size,
    /// Sequence parameter set, its header first.
    sequence: Vec<u8>,
    /// Picture parameter set, its header first.
    picture: Vec<u8>,
}

impl Track {
    /// Describes a track by the size of its pictures and its parameter sets.
    #[must_use]
    pub const fn new(size: Size, sequence: Vec<u8>, picture: Vec<u8>) -> Self {
        Self {
            size,
            sequence,
            picture,
        }
    }
}

impl Encoded for Track {
    fn encoded(&self) -> Vec<u8> {
        [
            self.sequence.clone(),
            self.picture.clone(),
            self.size.width().to_be_bytes().to_vec(),
        ]
        .concat()
    }
}

/// Picture of a track with its duration on the media clock.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Sample {
    /// Units of the picture, each after its length in four bytes.
    bytes: Vec<u8>,
    /// Duration in ticks of the media clock.
    duration: u32,
    /// Whether the picture is a key frame.
    key: bool,
}

impl Sample {
    /// Creates a sample from its units, its duration and whether it is a key frame.
    #[must_use]
    pub const fn new(bytes: Vec<u8>, duration: u32, key: bool) -> Self {
        Self {
            bytes,
            duration,
            key,
        }
    }
}

/// Media segment: one fragment of samples that follow each other.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Fragment {
    /// Number of the fragment in the stream.
    sequence: u32,
    /// Time of the first sample in ticks of the media clock.
    start: u64,
    /// Samples in the order of decoding.
    samples: Vec<Sample>,
}

impl Fragment {
    /// Creates a fragment from its number, the time of its first sample and its samples.
    #[must_use]
    pub const fn new(sequence: u32, start: u64, samples: Vec<Sample>) -> Self {
        Self {
            sequence,
            start,
            samples,
        }
    }
}

impl Encoded for Fragment {
    fn encoded(&self) -> Vec<u8> {
        self.samples
            .iter()
            .flat_map(|sample| {
                [
                    sample.bytes.clone(),
                    sample.duration.to_be_bytes().to_vec(),
                    vec![u8::from(sample.key)],
                ]
                .concat()
            })
            .chain(self.sequence.to_be_bytes())
            .chain(self.start.to_be_bytes())
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::{Encoded, Fragment, Sample, Track};
    use crate::domain::sps::Size;

    fn atoms(bytes: &[u8]) -> Vec<(String, Vec<u8>)> {
        let mut found = Vec::new();
        let mut rest = bytes;
        while let Some(size) = rest
            .get(..4)
            .map(|size| usize::try_from(u32::from_be_bytes(size.try_into().unwrap())).unwrap())
            .filter(|size| (8..=rest.len()).contains(size))
        {
            found.push((
                String::from_utf8_lossy(&rest[4..8]).into_owned(),
                rest[8..size].to_vec(),
            ));
            rest = &rest[size..];
        }
        found
    }

    fn after(bytes: &[u8], start: usize, end: usize) -> Vec<u8> {
        bytes.get(start..end.min(bytes.len())).unwrap_or_default().to_vec()
    }

    fn kinds(bytes: &[u8]) -> Vec<String> {
        atoms(bytes).into_iter().map(|(kind, _)| kind).collect()
    }

    fn inside(bytes: &[u8], kind: &str) -> Vec<u8> {
        atoms(bytes)
            .into_iter()
            .find(|(found, _)| found == kind)
            .map(|(_, body)| body)
            .unwrap_or_default()
    }

    fn init() -> Vec<u8> {
        Track::new(
            Size::new(640, 360),
            vec![0x67, 0x42, 0xC0, 0x1E, 0xD9],
            vec![0x68, 0xCB, 0x81],
        )
        .encoded()
    }

    fn table() -> Vec<u8> {
        let movie = inside(&init(), "moov");
        let media = inside(&inside(&movie, "trak"), "mdia");
        inside(&inside(&media, "minf"), "stbl")
    }

    fn entry() -> Vec<u8> {
        inside(&after(&inside(&table(), "stsd"), 8, usize::MAX), "avc1")
    }

    fn segment() -> Vec<u8> {
        Fragment::new(
            7,
            1_260_000,
            vec![
                Sample::new(vec![0, 0, 0, 2, 0x65, 0x88], 6000, true),
                Sample::new(vec![0, 0, 0, 1, 0x41], 6000, false),
            ],
        )
        .encoded()
    }

    fn run() -> Vec<u8> {
        inside(&inside(&inside(&segment(), "moof"), "traf"), "trun")
    }

    #[test]
    fn the_init_segment_is_a_file_type_and_a_movie_of_one_track() {
        let movie = inside(&init(), "moov");
        let track = inside(&movie, "trak");
        let media = inside(&track, "mdia");
        let information = inside(&media, "minf");
        assert_eq!(
            [
                kinds(&init()),
                kinds(&movie),
                kinds(&track),
                kinds(&media),
                kinds(&information),
                kinds(&table()),
                kinds(&after(&inside(&table(), "stsd"), 8, usize::MAX)),
                kinds(&after(&entry(), 78, usize::MAX)),
                kinds(&inside(&movie, "mvex")),
                kinds(&after(&inside(&inside(&information, "dinf"), "dref"), 8, usize::MAX)),
            ],
            [
                vec!["ftyp", "moov"],
                vec!["mvhd", "trak", "mvex"],
                vec!["tkhd", "mdia"],
                vec!["mdhd", "hdlr", "minf"],
                vec!["vmhd", "dinf", "stbl"],
                vec!["stsd", "stts", "stsc", "stsz", "stco"],
                vec!["avc1"],
                vec!["avcC"],
                vec!["trex"],
                vec!["url "],
            ]
        );
    }

    #[test]
    fn the_init_segment_carries_the_size_of_the_pictures() {
        let header = inside(&inside(&inside(&init(), "moov"), "trak"), "tkhd");
        assert_eq!(
            [after(&header, 76, 84), after(&entry(), 24, 28)],
            [
                vec![0x02, 0x80, 0, 0, 0x01, 0x68, 0, 0],
                vec![0x02, 0x80, 0x01, 0x68]
            ]
        );
    }

    #[test]
    fn the_init_segment_carries_the_parameter_sets() {
        assert_eq!(
            inside(&after(&entry(), 78, usize::MAX), "avcC"),
            [
                1, 0x42, 0xC0, 0x1E, 0xFF, 0xE1, 0, 5, 0x67, 0x42, 0xC0, 0x1E, 0xD9, 1, 0, 3, 0x68,
                0xCB, 0x81
            ]
        );
    }

    #[test]
    fn the_init_segment_counts_time_in_ninety_thousandths_of_a_second() {
        let movie = inside(&init(), "moov");
        let media = inside(&inside(&movie, "trak"), "mdia");
        assert_eq!(after(&inside(&media, "mdhd"), 12, 16), 90_000_u32.to_be_bytes());
    }

    #[test]
    fn a_media_segment_is_a_fragment_followed_by_its_data() {
        let fragment = inside(&segment(), "moof");
        assert_eq!(
            [
                kinds(&segment()),
                kinds(&fragment),
                kinds(&inside(&fragment, "traf")),
            ],
            [
                vec!["moof", "mdat"],
                vec!["mfhd", "traf"],
                vec!["tfhd", "tfdt", "trun"],
            ]
        );
        assert_eq!(
            inside(&segment(), "mdat"),
            [0, 0, 0, 2, 0x65, 0x88, 0, 0, 0, 1, 0x41]
        );
    }

    #[test]
    fn a_media_segment_carries_its_number_and_the_time_it_starts() {
        let fragment = inside(&segment(), "moof");
        assert_eq!(
            [
                inside(&fragment, "mfhd"),
                inside(&inside(&fragment, "traf"), "tfdt")
            ],
            [
                vec![0, 0, 0, 0, 0, 0, 0, 7],
                vec![1, 0, 0, 0, 0, 0, 0, 0, 0, 0x13, 0x39, 0xE0]
            ]
        );
    }

    #[test]
    fn a_media_segment_describes_every_sample_and_points_at_its_data() {
        let offset = u32::try_from(inside(&segment(), "moof").len() + 16).unwrap();
        assert_eq!(
            run(),
            [
                vec![0, 0, 0x07, 0x01, 0, 0, 0, 2],
                offset.to_be_bytes().to_vec(),
                vec![0, 0, 0x17, 0x70, 0, 0, 0, 6, 0x02, 0, 0, 0],
                vec![0, 0, 0x17, 0x70, 0, 0, 0, 5, 0x01, 0x01, 0, 0],
            ]
            .concat()
        );
    }

    #[test]
    fn a_media_segment_takes_the_track_from_the_fragment_box() {
        let fragment = inside(&inside(&segment(), "moof"), "traf");
        assert_eq!(inside(&fragment, "tfhd"), [0, 0x02, 0, 0, 0, 0, 0, 1]);
    }
}
