//! Sizes of pictures read from the sequence parameter sets of H.264.

use crate::domain::nal::{Nal, Unit};

/// Profiles whose sets carry the chroma format and the scaling lists.
const HIGH: [u32; 13] = [100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135];

/// Byte that follows two zero bytes only to prevent a start code.
const PREVENTION: u8 = 3;

/// Most leading zeros of an Exp-Golomb code whose number fits 32 bits.
const LONGEST: u32 = 31;

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
    /// Returns the width and the height in pixels.
    fn sides(&self) -> (u32, u32);
}

impl Sides for Size {
    fn sides(&self) -> (u32, u32) {
        (self.width, self.height)
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

impl SequenceSet {
    /// Returns the payload of the set without its header and the bytes that prevent start codes.
    fn payload(&self) -> Vec<u8> {
        self.unit
            .bytes()
            .iter()
            .skip(1)
            .fold((Vec::new(), 0), |(mut payload, zeros), &byte| {
                if zeros >= 2 && byte == PREVENTION {
                    return (payload, 0);
                }
                payload.push(byte);
                (payload, if byte == 0 { zeros + 1 } else { 0 })
            })
            .0
    }
}

impl Dimensioned for SequenceSet {
    fn size(&self) -> Result<Size, Unreadable> {
        let payload = self.payload();
        let (profile, bits) = Bits::new(&payload, 0).number(8)?;
        let (chroma, bits) = bits.skipped(16)?.golomb()?.1.chroma(profile)?;
        bits.golomb()?
            .1
            .order()?
            .golomb()?
            .1
            .skipped(1)?
            .picture(chroma)
    }
}

/// Length of one side of a picture before and after its crop.
#[derive(Debug, Clone, Copy)]
struct Span {
    /// Length of the side as coded, in whole macroblocks.
    whole: u64,
    /// Length cut off the side.
    crop: u64,
}

impl Span {
    /// Creates a span from the coded length and the length cut off it.
    const fn new(whole: u64, crop: u64) -> Self {
        Self { whole, crop }
    }
}

/// Length of a side in pixels.
trait Pixels {
    /// Returns the length left after the crop, or why there is none.
    fn pixels(&self) -> Result<u32, Unreadable>;
}

impl Pixels for Span {
    fn pixels(&self) -> Result<u32, Unreadable> {
        self.whole
            .checked_sub(self.crop)
            .and_then(|rest| u32::try_from(rest).ok())
            .ok_or(Unreadable::Broken)
    }
}

/// Bits of a payload read one after another, from the most significant.
#[derive(Debug, Clone, Copy)]
struct Bits<'a> {
    /// Bytes of the payload.
    bytes: &'a [u8],
    /// Number of bits already read.
    position: usize,
}

impl<'a> Bits<'a> {
    /// Points at the bit with the given number.
    const fn new(bytes: &'a [u8], position: usize) -> Self {
        Self { bytes, position }
    }
}

/// Values read from the bits of a payload, each with the bits that follow it.
trait Reading: Sized {
    /// Returns the next bit as a flag.
    fn flag(self) -> Result<(bool, Self), Unreadable>;
    /// Returns the number written in the given count of bits.
    fn number(self, count: u32) -> Result<(u32, Self), Unreadable>;
    /// Returns the bits after the given count of bits.
    fn skipped(self, count: u32) -> Result<Self, Unreadable>;
    /// Returns the unsigned number written in the Exp-Golomb code.
    fn golomb(self) -> Result<(u32, Self), Unreadable>;
    /// Returns the signed number written in the Exp-Golomb code.
    fn signed(self) -> Result<(i64, Self), Unreadable>;
}

impl Reading for Bits<'_> {
    fn flag(self) -> Result<(bool, Self), Unreadable> {
        let byte = self.bytes.get(self.position / 8).ok_or(Unreadable::Short)?;
        Ok((
            (byte >> (7 - self.position % 8)) & 1 == 1,
            Self::new(self.bytes, self.position + 1),
        ))
    }

    fn number(self, count: u32) -> Result<(u32, Self), Unreadable> {
        (0..count).try_fold((0, self), |(value, bits), _| {
            let (flag, bits) = bits.flag()?;
            Ok((value * 2 + u32::from(flag), bits))
        })
    }

    fn skipped(self, count: u32) -> Result<Self, Unreadable> {
        Ok(self.number(count)?.1)
    }

    fn golomb(self) -> Result<(u32, Self), Unreadable> {
        let mut zeros = 0;
        let mut bits = self;
        loop {
            let (flag, rest) = bits.flag()?;
            bits = rest;
            if flag {
                break;
            }
            zeros += 1;
            if zeros > LONGEST {
                return Err(Unreadable::Broken);
            }
        }
        let (suffix, bits) = bits.number(zeros)?;
        Ok(((1 << zeros) - 1 + suffix, bits))
    }

    fn signed(self) -> Result<(i64, Self), Unreadable> {
        let (code, bits) = self.golomb()?;
        let half = i64::from(code.div_ceil(2));
        Ok((if code % 2 == 1 { half } else { -half }, bits))
    }
}

/// Fields of a sequence parameter set read from its bits.
trait Fields: Sized {
    /// Returns the chroma format, zero for separate planes, and the bits after it.
    fn chroma(self, profile: u32) -> Result<(u32, Self), Unreadable>;
    /// Returns the bits after the given count of scaling lists.
    fn lists(self, count: usize) -> Result<Self, Unreadable>;
    /// Returns the bits after one scaling list of the given length.
    fn list(self, length: usize) -> Result<Self, Unreadable>;
    /// Returns the bits after the fields of the order of pictures.
    fn order(self) -> Result<Self, Unreadable>;
    /// Returns the size of the picture in a stream of the chroma format.
    fn picture(self, chroma: u32) -> Result<Size, Unreadable>;
    /// Returns the offsets of the crop: left, right, top and bottom.
    fn crop(self) -> Result<[u64; 4], Unreadable>;
}

impl Fields for Bits<'_> {
    fn chroma(self, profile: u32) -> Result<(u32, Self), Unreadable> {
        if !HIGH.contains(&profile) {
            return Ok((1, self));
        }
        let (format, bits) = self.golomb()?;
        let (separate, bits) = if format == 3 {
            bits.flag()?
        } else {
            (false, bits)
        };
        let (scaled, bits) = bits.golomb()?.1.golomb()?.1.skipped(1)?.flag()?;
        let bits = if scaled {
            bits.lists(if format == 3 { 12 } else { 8 })?
        } else {
            bits
        };
        Ok((if separate { 0 } else { format }, bits))
    }

    fn lists(self, count: usize) -> Result<Self, Unreadable> {
        (0..count).try_fold(self, |bits, index| {
            let (present, bits) = bits.flag()?;
            if present {
                bits.list(if index < 6 { 16 } else { 64 })
            } else {
                Ok(bits)
            }
        })
    }

    fn list(self, length: usize) -> Result<Self, Unreadable> {
        (0..length)
            .try_fold((8, 8, self), |(last, next, bits), _| {
                if next == 0 {
                    return Ok((last, 0, bits));
                }
                let (delta, bits) = bits.signed()?;
                let next = (last + delta).rem_euclid(256);
                Ok((if next == 0 { last } else { next }, next, bits))
            })
            .map(|(_, _, bits)| bits)
    }

    fn order(self) -> Result<Self, Unreadable> {
        let (kind, bits) = self.golomb()?;
        match kind {
            0 => Ok(bits.golomb()?.1),
            1 => {
                let (count, bits) = bits.skipped(1)?.signed()?.1.signed()?.1.golomb()?;
                (0..count).try_fold(bits, |bits, _| Ok(bits.signed()?.1))
            }
            _ => Ok(bits),
        }
    }

    fn picture(self, chroma: u32) -> Result<Size, Unreadable> {
        let (columns, bits) = self.golomb()?;
        let (rows, bits) = bits.golomb()?;
        let (progressive, bits) = bits.flag()?;
        let bits = if progressive { bits } else { bits.skipped(1)? };
        let (cropped, bits) = bits.skipped(1)?.flag()?;
        let [left, right, top, bottom] = if cropped { bits.crop()? } else { [0; 4] };
        let fields = if progressive { 1 } else { 2 };
        let (across, down) = match chroma {
            1 => (2, 2 * fields),
            2 => (2, fields),
            _ => (1, fields),
        };
        Ok(Size::new(
            Span::new((u64::from(columns) + 1) * 16, across * (left + right)).pixels()?,
            Span::new(fields * (u64::from(rows) + 1) * 16, down * (top + bottom)).pixels()?,
        ))
    }

    fn crop(self) -> Result<[u64; 4], Unreadable> {
        let (left, bits) = self.golomb()?;
        let (right, bits) = bits.golomb()?;
        let (top, bits) = bits.golomb()?;
        let (bottom, _) = bits.golomb()?;
        Ok([left, right, top, bottom].map(u64::from))
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
    fn keeps_a_three_that_follows_no_zeros() {
        let set = crafted(
            [0x67, 0x42, 0xC0, 0x03],
            "1 1 011 010 0 00000101000 000010111 1 1 1 1 010 1 00101",
        );
        assert_eq!(set.size(), Ok(Size::new(638, 360)));
    }

    #[test]
    fn reads_the_longest_number_that_fits() {
        let set = crafted(
            [0x67, 0x42, 0xC0, 0x1E],
            &format!(
                "{}1{} 1 011 010 0 00000101000 000010111 1 1 1 1 010 1 00101",
                "0".repeat(31),
                "0".repeat(31)
            ),
        );
        assert_eq!(set.size(), Ok(Size::new(638, 360)));
    }

    #[test]
    fn skips_scaling_lists_read_to_their_end() {
        let set = crafted(
            [0x67, 0x64, 0x00, 0x1E],
            &format!(
                "1 010 1 1 0 1 1{} 00000 1{} 0 \
                 1 011 010 0 00000101000 000010111 1 1 1 1 010 1 00101",
                "1".repeat(16),
                "1".repeat(64)
            ),
        );
        assert_eq!(set.size(), Ok(Size::new(638, 360)));
    }

    #[test]
    fn crops_rows_of_both_fields_in_four_two_zero() {
        let set = crafted(
            [0x67, 0x42, 0xC0, 0x1E],
            "1 1 011 010 0 00000101000 000010001 0 0 1 1 1 1 1 010",
        );
        assert_eq!(set.size(), Ok(Size::new(640, 540)));
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
        let set = crafted(
            [0x67, 0x42, 0xC0, 0x1E],
            "1 1 011 010 0 1 1 1 1 1 1 000000001 11110000 1 1",
        );
        assert_eq!(set.size(), Err(Unreadable::Broken));
    }

    #[test]
    fn tells_its_sides() {
        assert_eq!(Size::new(640, 360).sides(), (640, 360));
    }
}
