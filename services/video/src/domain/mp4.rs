//! Fragmented MP4 of one H.264 track: the init segment and the media segments.

use crate::domain::sps::{Sides, Size};

/// Bytes of a piece of a file.
pub trait Encoded {
    /// Returns the bytes of the piece.
    fn encoded(&self) -> Vec<u8>;
}

/// Ticks of the media clock in one second.
pub const TIMESCALE: u32 = 90_000;

/// Brands of the file: ISO base media with fragments and H.264.
const FILE_TYPE: [u8; 24] = [
    0x69, 0x73, 0x6F, 0x6D, 0x00, 0x00, 0x02, 0x00, 0x69, 0x73, 0x6F, 0x6D, 0x69, 0x73, 0x6F, 0x36,
    0x61, 0x76, 0x63, 0x31, 0x6D, 0x70, 0x34, 0x31,
];

/// Ticks of the clock of the whole movie in one second.
const MOVIE_TIMESCALE: [u8; 4] = [0, 0, 0x03, 0xE8];

/// Number of the only track.
const TRACK: [u8; 4] = [0, 0, 0, 1];

/// Number the movie keeps for a track it does not have yet.
const NEXT_TRACK: [u8; 4] = [0, 0, 0, 2];

/// Matrix that leaves the pictures as they are.
const MATRIX: [u8; 36] = [
    0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0x40, 0, 0, 0,
];

/// Undetermined language of the media, packed as the format wants it.
const LANGUAGE: [u8; 4] = [0x55, 0xC4, 0, 0];

/// Body of the handler that marks the track as video.
const HANDLER: [u8; 37] = [
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x76, 0x69, 0x64, 0x65, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x56, 0x69, 0x64, 0x65, 0x6F, 0x48, 0x61, 0x6E,
    0x64, 0x6C, 0x65, 0x72, 0x00,
];

/// Body of the data information: the samples are in the same file.
const REFERENCES: [u8; 28] = [
    0x00, 0x00, 0x00, 0x1C, 0x64, 0x72, 0x65, 0x66, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01,
    0x00, 0x00, 0x00, 0x0C, 0x75, 0x72, 0x6C, 0x20, 0x00, 0x00, 0x00, 0x01,
];

/// Resolution of 72 dots per inch.
const RESOLUTION: [u8; 4] = [0, 0x48, 0, 0];

/// Length of the header of a box: its size and its kind.
const HEADER: usize = 8;

/// Flags of a trun box: a data offset and a duration, size and flags per sample.
const RUN: [u8; 4] = [0, 0, 0x07, 0x01];

/// Flags of a sample that depends on no other picture.
const KEY: [u8; 4] = [0x02, 0, 0, 0];

/// Flags of a sample that depends on others and starts nothing.
const DEPENDENT: [u8; 4] = [0x01, 0x01, 0, 0];

/// Box of the MP4 format: its kind and its body.
#[derive(Debug, Clone, PartialEq, Eq)]
struct Atom {
    /// Four letters of the kind.
    kind: [u8; 4],
    /// Bytes that follow the header.
    body: Vec<u8>,
}

impl Atom {
    /// Creates a box of the kind with the body.
    const fn new(kind: [u8; 4], body: Vec<u8>) -> Self {
        Self { kind, body }
    }
}

impl Encoded for Atom {
    fn encoded(&self) -> Vec<u8> {
        [
            &u32::try_from(self.body.len() + HEADER)
                .unwrap_or(u32::MAX)
                .to_be_bytes()[..],
            &self.kind,
            &self.body,
        ]
        .concat()
    }
}

/// Number written in two bytes, the largest one when it does not fit.
#[derive(Debug, Clone, Copy)]
struct Short {
    /// The number.
    number: usize,
}

impl Short {
    /// Wraps the number.
    const fn new(number: usize) -> Self {
        Self { number }
    }
}

impl Encoded for Short {
    fn encoded(&self) -> Vec<u8> {
        u16::try_from(self.number)
            .unwrap_or(u16::MAX)
            .to_be_bytes()
            .to_vec()
    }
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

impl Track {
    /// Returns the box of the track with its header and its media.
    fn track(&self) -> Atom {
        let (width, height) = self.size.sides();
        let header = Atom::new(
            *b"tkhd",
            [
                &[0, 0, 0, 3][..],
                &[0; 8],
                &TRACK,
                &[0; 24],
                &MATRIX,
                &(width << 16).to_be_bytes(),
                &(height << 16).to_be_bytes(),
            ]
            .concat(),
        );
        let media = Atom::new(
            *b"mdhd",
            [&[0; 12][..], &TIMESCALE.to_be_bytes(), &[0; 4], &LANGUAGE].concat(),
        );
        let handler = Atom::new(*b"hdlr", HANDLER.to_vec());
        let information = Atom::new(
            *b"minf",
            [
                Atom::new(*b"vmhd", [&[0, 0, 0, 1][..], &[0; 8]].concat()).encoded(),
                Atom::new(*b"dinf", REFERENCES.to_vec()).encoded(),
                self.table().encoded(),
            ]
            .concat(),
        );
        Atom::new(
            *b"trak",
            [
                header.encoded(),
                Atom::new(
                    *b"mdia",
                    [media.encoded(), handler.encoded(), information.encoded()].concat(),
                )
                .encoded(),
            ]
            .concat(),
        )
    }

    /// Returns the table of samples, empty but for the description of the pictures.
    fn table(&self) -> Atom {
        Atom::new(
            *b"stbl",
            [
                Atom::new(
                    *b"stsd",
                    [&[0, 0, 0, 0, 0, 0, 0, 1][..], &self.entry().encoded()].concat(),
                )
                .encoded(),
                Atom::new(*b"stts", vec![0; 8]).encoded(),
                Atom::new(*b"stsc", vec![0; 8]).encoded(),
                Atom::new(*b"stsz", vec![0; 12]).encoded(),
                Atom::new(*b"stco", vec![0; 8]).encoded(),
            ]
            .concat(),
        )
    }

    /// Returns the description of the H.264 pictures with their parameter sets.
    fn entry(&self) -> Atom {
        let (width, height) = self.size.sides();
        let configuration = Atom::new(
            *b"avcC",
            [
                &[1][..],
                &self
                    .sequence
                    .iter()
                    .skip(1)
                    .take(3)
                    .copied()
                    .collect::<Vec<u8>>(),
                &[0xFF, 0xE1],
                &Short::new(self.sequence.len()).encoded(),
                &self.sequence,
                &[1],
                &Short::new(self.picture.len()).encoded(),
                &self.picture,
            ]
            .concat(),
        );
        Atom::new(
            *b"avc1",
            [
                &[0, 0, 0, 0, 0, 0, 0, 1][..],
                &[0; 16],
                &Short::new(usize::try_from(width).unwrap_or(usize::MAX)).encoded(),
                &Short::new(usize::try_from(height).unwrap_or(usize::MAX)).encoded(),
                &RESOLUTION,
                &RESOLUTION,
                &[0, 0, 0, 0, 0, 1],
                &[0; 32],
                &[0, 0x18, 0xFF, 0xFF],
                &configuration.encoded(),
            ]
            .concat(),
        )
    }
}

impl Encoded for Track {
    fn encoded(&self) -> Vec<u8> {
        let movie = Atom::new(
            *b"mvhd",
            [
                &[0; 12][..],
                &MOVIE_TIMESCALE,
                &[0; 4],
                &[0, 1, 0, 0, 1, 0],
                &[0; 10],
                &MATRIX,
                &[0; 24],
                &NEXT_TRACK,
            ]
            .concat(),
        );
        let extends = Atom::new(
            *b"mvex",
            Atom::new(
                *b"trex",
                [&[0; 4][..], &TRACK, &[0, 0, 0, 1], &[0; 12]].concat(),
            )
            .encoded(),
        );
        [
            Atom::new(*b"ftyp", FILE_TYPE.to_vec()).encoded(),
            Atom::new(
                *b"moov",
                [movie.encoded(), self.track().encoded(), extends.encoded()].concat(),
            )
            .encoded(),
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

/// Media segment made of one fragment of samples that follow each other.
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

impl Fragment {
    /// Returns the box of the fragment whose run points at the data after the offset.
    fn movie(&self, offset: usize) -> Atom {
        let track = Atom::new(
            *b"traf",
            [
                Atom::new(*b"tfhd", [&[0, 0x02, 0, 0][..], &TRACK].concat()).encoded(),
                Atom::new(
                    *b"tfdt",
                    [&[1, 0, 0, 0][..], &self.start.to_be_bytes()].concat(),
                )
                .encoded(),
                self.run(offset).encoded(),
            ]
            .concat(),
        );
        Atom::new(
            *b"moof",
            [
                Atom::new(
                    *b"mfhd",
                    [&[0; 4][..], &self.sequence.to_be_bytes()].concat(),
                )
                .encoded(),
                track.encoded(),
            ]
            .concat(),
        )
    }

    /// Returns the run of the samples that points at their data after the offset.
    fn run(&self, offset: usize) -> Atom {
        let samples: Vec<u8> = self
            .samples
            .iter()
            .flat_map(|sample| {
                [
                    sample.duration.to_be_bytes(),
                    u32::try_from(sample.bytes.len())
                        .unwrap_or(u32::MAX)
                        .to_be_bytes(),
                    if sample.key { KEY } else { DEPENDENT },
                ]
                .concat()
            })
            .collect();
        Atom::new(
            *b"trun",
            [
                &RUN[..],
                &u32::try_from(self.samples.len())
                    .unwrap_or(u32::MAX)
                    .to_be_bytes(),
                &u32::try_from(offset).unwrap_or(u32::MAX).to_be_bytes(),
                &samples,
            ]
            .concat(),
        )
    }
}

impl Encoded for Fragment {
    fn encoded(&self) -> Vec<u8> {
        let offset = self.movie(0).encoded().len() + HEADER;
        [
            self.movie(offset).encoded(),
            Atom::new(
                *b"mdat",
                self.samples
                    .iter()
                    .flat_map(|sample| sample.bytes.iter().copied())
                    .collect(),
            )
            .encoded(),
        ]
        .concat()
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
        bytes
            .get(start..end.min(bytes.len()))
            .unwrap_or_default()
            .to_vec()
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
                kinds(&after(
                    &inside(&inside(&information, "dinf"), "dref"),
                    8,
                    usize::MAX
                )),
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
        assert_eq!(
            after(&inside(&media, "mdhd"), 12, 16),
            90_000_u32.to_be_bytes()
        );
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
