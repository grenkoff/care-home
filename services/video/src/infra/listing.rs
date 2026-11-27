//! Streams of the service as its setting lists them.

use retina::client::Credentials;
use url::Url;

use crate::infra::address::Address;

/// Longest key of a stream, as long as the key a camera keeps in core.
const KEY_LENGTH: usize = 64;

/// Name of the demo source in the setting.
const DEMO: &str = "demo";

/// Scheme of the address of a camera.
const RTSP: &str = "rtsp";

/// Source of the pictures of a stream.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Source {
    /// The committed test pattern played in a loop.
    Demo,
    /// An IP camera that serves H.264 over RTSP.
    Camera(Address),
}

/// Why the setting of the streams cannot be read.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum Misconfigured {
    /// The entry at the position, counted from one, has no source after its key.
    #[error("the entry {0} of the setting names no source, write it as key=source")]
    Unsourced(usize),
    /// An entry names a source the service does not know.
    #[error("the stream `{0}` has an unknown source")]
    Unknown(String),
    /// The key of the entry at the position is empty, too long or not a slug.
    #[error(
        "the key of the entry {0} of the setting is not a slug of at most {KEY_LENGTH} characters"
    )]
    Key(usize),
    /// Two entries have the same key.
    #[error("the stream `{0}` is listed twice")]
    Twice(String),
}

/// Streams of the service with their sources.
pub trait Configured {
    /// Returns every stream with its source, or why the setting is wrong.
    fn streams(&self) -> Result<Vec<(String, Source)>, Misconfigured>;
}

/// Setting that lists the streams as `key=source` entries split by commas.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Listing {
    /// Text of the setting.
    text: String,
}

impl Listing {
    /// Wraps the text of the setting.
    #[must_use]
    pub fn new(text: impl Into<String>) -> Self {
        Self { text: text.into() }
    }
}

impl Configured for Listing {
    fn streams(&self) -> Result<Vec<(String, Source)>, Misconfigured> {
        self.text
            .split(',')
            .map(str::trim)
            .filter(|entry| !entry.is_empty())
            .zip(1..)
            .try_fold(
                Vec::new(),
                |streams: Vec<(String, Source)>, (entry, position)| {
                    let (key, source) = entry
                        .split_once('=')
                        .ok_or(Misconfigured::Unsourced(position))?;
                    let key = key.trim();
                    let slug = key.chars().all(|letter| {
                        letter.is_ascii_alphanumeric() || letter == '-' || letter == '_'
                    });
                    if key.is_empty() || key.len() > KEY_LENGTH || !slug {
                        return Err(Misconfigured::Key(position));
                    }
                    if streams.iter().any(|(known, _)| known == key) {
                        return Err(Misconfigured::Twice(key.to_owned()));
                    }
                    let source = Written {
                        key,
                        text: source.trim(),
                    }
                    .source()?;
                    Ok(streams
                        .into_iter()
                        .chain([(key.to_owned(), source)])
                        .collect())
                },
            )
    }
}

/// Source that a text of the setting names.
trait Named {
    /// Returns the source the text names, or why it names none.
    fn source(&self) -> Result<Source, Misconfigured>;
}

/// Text of the source of one stream, with the key of the stream.
struct Written<'a> {
    /// Key of the stream.
    key: &'a str,
    /// Text of its source.
    text: &'a str,
}

impl Named for Written<'_> {
    fn source(&self) -> Result<Source, Misconfigured> {
        if self.text == DEMO {
            return Ok(Source::Demo);
        }
        let unknown = || Misconfigured::Unknown(self.key.to_owned());
        let mut location = Url::parse(self.text).map_err(|_| unknown())?;
        if location.scheme() != RTSP || location.host_str().is_none_or(str::is_empty) {
            return Err(unknown());
        }
        let credentials = if location.username().is_empty() && location.password().is_none() {
            None
        } else {
            Some(Credentials {
                username: Escaped(location.username()).decoded().ok_or_else(unknown)?,
                password: Escaped(location.password().unwrap_or_default())
                    .decoded()
                    .ok_or_else(unknown)?,
            })
        };
        location.set_username("").map_err(|()| unknown())?;
        location.set_password(None).map_err(|()| unknown())?;
        Ok(Source::Camera(Address::new(location, credentials)))
    }
}

/// Text that percent escapes can be taken out of.
trait Decoded {
    /// Returns the text with its escapes decoded, when they are whole and spell UTF-8.
    fn decoded(&self) -> Option<String>;
}

/// Part of an address written with percent escapes.
struct Escaped<'a>(&'a str);

impl Decoded for Escaped<'_> {
    fn decoded(&self) -> Option<String> {
        let mut pieces = self.0.split('%');
        let first = pieces.next().unwrap_or_default().as_bytes().to_vec();
        let bytes = pieces.try_fold(first, |bytes, piece| {
            let byte = piece
                .get(..2)
                .filter(|digits| digits.bytes().all(|digit| digit.is_ascii_hexdigit()))
                .and_then(|digits| u8::from_str_radix(digits, 16).ok())?;
            Some(
                bytes
                    .into_iter()
                    .chain([byte])
                    .chain(piece.bytes().skip(2))
                    .collect(),
            )
        })?;
        String::from_utf8(bytes).ok()
    }
}

#[cfg(test)]
mod tests {
    use retina::client::Credentials;
    use url::Url;

    use super::{Configured, Listing, Misconfigured, Source};
    use crate::infra::address::Address;

    #[test]
    fn lists_a_camera_with_its_address() {
        let listed = Listing::new(
            "porch=rtsp://keeper:se%2Ccret@10.0.0.21:554/stream1?channel=1, roof=rtsp://camera.home/live",
        )
        .streams();
        let porch = Url::parse("rtsp://10.0.0.21:554/stream1?channel=1").unwrap();
        let roof = Url::parse("rtsp://camera.home/live").unwrap();
        let keeper = Credentials {
            username: String::from("keeper"),
            password: String::from("se,cret"),
        };
        assert_eq!(
            listed,
            Ok(vec![
                (
                    String::from("porch"),
                    Source::Camera(Address::new(porch, Some(keeper)))
                ),
                (
                    String::from("roof"),
                    Source::Camera(Address::new(roof, None))
                ),
            ])
        );
    }

    #[test]
    fn lists_every_stream_with_its_source() {
        assert_eq!(
            Listing::new(" hall=demo, garden_2=demo ,dining-room=demo").streams(),
            Ok(vec![
                (String::from("hall"), Source::Demo),
                (String::from("garden_2"), Source::Demo),
                (String::from("dining-room"), Source::Demo),
            ])
        );
    }

    #[test]
    fn lists_no_streams_for_an_empty_setting() {
        assert_eq!(Listing::new(" , ").streams(), Ok(Vec::new()));
    }

    #[test]
    fn refuses_an_entry_without_a_source() {
        assert_eq!(
            Listing::new("hall=demo, ,garden").streams(),
            Err(Misconfigured::Unsourced(2))
        );
    }

    #[test]
    fn never_shows_the_password_of_a_refused_entry() {
        let shown = [
            "rtsp://keeper:secret@10.0.0.21/stream1?channel=1",
            "hall=demo,porch=rtsp://keeper:se,cret@10.0.0.21/stream1",
            "porch:rtsp://keeper:secret@10.0.0.21/stream1",
            "porch=rtsp://keeper:secret@10.0.0.21:99999/stream1",
        ]
        .map(|text| {
            Listing::new(text).streams().map_err(|refusal| {
                refusal.to_string().contains("secret") || refusal.to_string().contains("cret")
            })
        });
        assert_eq!(shown, [Err(false), Err(false), Err(false), Err(false)]);
    }

    #[test]
    fn refuses_a_source_it_does_not_know() {
        let refused = [
            "hall=webcam",
            "hall=http://10.0.0.21/stream1",
            "hall=rtsp://",
            "hall=rtsp://keeper:%FF@10.0.0.21/stream1",
            "hall=rtsp://keeper:%2@10.0.0.21/stream1",
        ];
        assert_eq!(
            refused.map(|text| Listing::new(text).streams()),
            refused.map(|_| Err(Misconfigured::Unknown(String::from("hall"))))
        );
    }

    #[test]
    fn refuses_a_key_that_is_not_a_slug() {
        let long = "k".repeat(65);
        assert_eq!(
            [
                Listing::new("=demo").streams(),
                Listing::new("hall=demo,main hall=demo").streams(),
                Listing::new(format!("hall=demo,garden=demo,{long}=demo")).streams(),
                Listing::new(format!("{}=demo", "k".repeat(64))).streams(),
            ],
            [
                Err(Misconfigured::Key(1)),
                Err(Misconfigured::Key(2)),
                Err(Misconfigured::Key(3)),
                Ok(vec![("k".repeat(64), Source::Demo)]),
            ]
        );
    }

    #[test]
    fn refuses_a_stream_listed_twice() {
        assert_eq!(
            Listing::new("hall=demo,hall=demo").streams(),
            Err(Misconfigured::Twice(String::from("hall")))
        );
    }
}
