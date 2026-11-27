//! Sizes of pictures read from the sequence parameter sets of H.264.

use crate::domain::nal::{Nal, Unit};

/// Why a sequence parameter set cannot be read.
#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
pub enum Unreadable {
    /// The set ends before the size of the picture.
    #[error("the sequence parameter set ends too early")]
    Short,
    /// The set holds a number that no picture has.
    #[error("the sequence parameter set holds an impossible number")]
    Broken,
}

/// Size of a picture in pixels.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Size {
    /// Width in pixels.
    width: u32,
    /// Height in pixels.
    height: u32,
}

impl Size {
    /// Creates a size from its width and height in pixels.
    #[must_use]
    pub const fn new(width: u32, height: u32) -> Self {
        Self { width, height }
    }
}

/// Sides of a picture.
pub trait Sides {
    /// Returns the width in pixels.
    fn width(&self) -> u32;
    /// Returns the height in pixels.
    fn height(&self) -> u32;
}

impl Sides for Size {
    fn width(&self) -> u32 {
        self.width
    }

    fn height(&self) -> u32 {
        self.height
    }
}

/// Source of the size of the pictures of a stream.
pub trait Dimensioned {
    /// Returns the size of every picture, or why it cannot be read.
    fn size(&self) -> Result<Size, Unreadable>;
}

/// Sequence parameter set of an H.264 stream.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SequenceSet {
    /// Unit that carries the set.
    unit: Unit,
}

impl SequenceSet {
    /// Wraps the unit that carries the set.
    #[must_use]
    pub const fn new(unit: Unit) -> Self {
        Self { unit }
    }
}

impl Dimensioned for SequenceSet {
    fn size(&self) -> Result<Size, Unreadable> {
        Ok(Size::new(
            u32::try_from(self.unit.bytes().len()).unwrap_or_default(),
            0,
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::{Dimensioned, SequenceSet, Sides, Size, Unreadable};
    use crate::domain::nal::Unit;

    fn crafted(header: [u8; 4], bits: &str) -> SequenceSet {
        let digits: Vec<u8> = bits
            .bytes()
            .filter(|digit| *digit != b' ')
            .map(|digit| digit - b'0')
            .collect();
        let packed = digits.chunks(8).map(|chunk| {
            chunk
                .iter()
                .enumerate()
                .fold(0, |byte, (index, bit)| byte | bit << (7 - index))
        });
        SequenceSet::new(Unit::new(header.into_iter().chain(packed).collect()))
    }

    #[test]
    fn reads_the_size_of_the_demo_pattern() {
        let set = SequenceSet::new(Unit::new(vec![
            0x67, 0x42, 0xC0, 0x1E, 0xD9, 0x00, 0xA0, 0x2F, 0xF9, 0x70, 0x11, 0x00, 0x00, 0x03,
            0x00, 0x01, 0x00, 0x00, 0x03, 0x00, 0x1E, 0x0F, 0x16, 0x2E, 0x48,
        ]));
        assert_eq!(set.size(), Ok(Size::new(640, 360)));
    }

    #[test]
    fn reads_the_size_of_an_interlaced_high_stream_in_four_two_two() {
        let set = SequenceSet::new(Unit::new(vec![
            0x67, 0x7A, 0x00, 0x28, 0xBC, 0xD9, 0x40, 0x78, 0x04, 0x4F, 0xCB, 0x80, 0x88, 0x00,
            0x00, 0x03, 0x00, 0x08, 0x00, 0x00, 0x03, 0x01, 0x90, 0xF8, 0xB1, 0x6C, 0xB0,
        ]));
        assert_eq!(set.size(), Ok(Size::new(1920, 1080)));
    }

    #[test]
    fn drops_the_bytes_that_prevent_start_codes() {
        let set = SequenceSet::new(Unit::new(vec![
            0x67, 0x42, 0x00, 0x00, 0x03, 0xD9, 0x00, 0xA0, 0x2F, 0xF9, 0x70,
        ]));
        assert_eq!(set.size(), Ok(Size::new(640, 360)));
    }

    #[test]
    fn crops_pairs_of_columns_in_four_two_zero() {
        let set = crafted(
            [0x67, 0x42, 0xC0, 0x1E],
            "1 1 011 010 0 00000101000 000010111 1 1 1 1 010 1 00101",
        );
        assert_eq!(set.size(), Ok(Size::new(638, 360)));
    }

    #[test]
    fn crops_pairs_of_columns_and_single_rows_in_four_two_two() {
        let set = crafted(
            [0x67, 0x7A, 0x00, 0x1E],
            "1 011 1 1 0 0 1 1 1 010 0 00000101000 000010111 1 1 1 1 010 1 0001001",
        );
        assert_eq!(set.size(), Ok(Size::new(638, 360)));
    }

    #[test]
    fn crops_single_pixels_of_separate_planes_after_scaling_lists_and_an_order_cycle() {
        let set = crafted(
            [0x67, 0xF4, 0x00, 0x1E],
            "1 00100 1 1 1 0 1 1 010 000010011 00000 1 000010001 00000 \
             1 010 0 1 1 011 010 011 010 0 00000101000 000010111 1 1 1 1 011 1 0001001",
        );
        assert_eq!(set.size(), Ok(Size::new(638, 360)));
    }

    #[test]
    fn crops_rows_of_both_fields_of_a_monochrome_stream() {
        let set = crafted(
            [0x67, 0x64, 0x00, 0x1E],
            "1 1 1 1 0 0 1 011 010 0 00000101000 000010001 0 0 1 1 010 1 1 011",
        );
        assert_eq!(set.size(), Ok(Size::new(639, 540)));
    }

    #[test]
    fn refuses_a_set_that_ends_too_early() {
        let set = SequenceSet::new(Unit::new(vec![0x67, 0x42, 0xC0]));
        assert_eq!(set.size(), Err(Unreadable::Short));
    }

    #[test]
    fn refuses_a_number_too_large_for_a_picture() {
        let set = crafted([0x67, 0x42, 0xC0, 0x1E], &format!("{}1", "0".repeat(40)));
        assert_eq!(set.size(), Err(Unreadable::Broken));
    }

    #[test]
    fn refuses_a_crop_larger_than_the_picture() {
        let set = crafted([0x67, 0x42, 0xC0, 0x1E], "1 1 011 010 0 1 1 1 1 1 1 000000001 11110000 1 1");
        assert_eq!(set.size(), Err(Unreadable::Broken));
    }

    #[test]
    fn tells_its_sides() {
        let size = Size::new(640, 360);
        assert_eq!((size.width(), size.height()), (640, 360));
    }
}
