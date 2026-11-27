//! Streams of the service as its setting lists them.

/// Longest key of a stream, as long as the key a camera keeps in core.
const KEY_LENGTH: usize = 64;

/// Name of the demo source in the setting.
const DEMO: &str = "demo";

/// Source of the pictures of a stream.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Source {
    /// The committed test pattern played in a loop.
    Demo,
}

/// Why the setting of the streams cannot be read.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum Misconfigured {
    /// An entry has no source after its key.
    #[error("the stream `{0}` names no source, write it as key=source")]
    Unsourced(String),
    /// An entry names a source the service does not know.
    #[error("the stream `{0}` has an unknown source")]
    Unknown(String),
    /// A key is empty, too long or has more than letters, digits, hyphens and underscores.
    #[error("the key `{0}` of a stream is not a slug of at most {KEY_LENGTH} characters")]
    Key(String),
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
            .try_fold(Vec::new(), |streams: Vec<(String, Source)>, entry| {
                let (key, source) = entry
                    .split_once('=')
                    .ok_or_else(|| Misconfigured::Unsourced(entry.to_owned()))?;
                let key = key.trim();
                let slug = key
                    .chars()
                    .all(|letter| letter.is_ascii_alphanumeric() || letter == '-' || letter == '_');
                if key.is_empty() || key.len() > KEY_LENGTH || !slug {
                    return Err(Misconfigured::Key(key.to_owned()));
                }
                if streams.iter().any(|(known, _)| known == key) {
                    return Err(Misconfigured::Twice(key.to_owned()));
                }
                let source = match source.trim() {
                    DEMO => Source::Demo,
                    _ => return Err(Misconfigured::Unknown(key.to_owned())),
                };
                Ok(streams
                    .into_iter()
                    .chain([(key.to_owned(), source)])
                    .collect())
            })
    }
}

#[cfg(test)]
mod tests {
    use super::{Configured, Listing, Misconfigured, Source};

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
            Listing::new("hall=demo,garden").streams(),
            Err(Misconfigured::Unsourced(String::from("garden")))
        );
    }

    #[test]
    fn refuses_a_source_it_does_not_know() {
        assert_eq!(
            Listing::new("hall=webcam").streams(),
            Err(Misconfigured::Unknown(String::from("hall")))
        );
    }

    #[test]
    fn refuses_a_key_that_is_not_a_slug() {
        let long = "k".repeat(65);
        assert_eq!(
            [
                Listing::new("=demo").streams(),
                Listing::new("main hall=demo").streams(),
                Listing::new(format!("{long}=demo")).streams(),
                Listing::new(format!("{}=demo", "k".repeat(64))).streams(),
            ],
            [
                Err(Misconfigured::Key(String::new())),
                Err(Misconfigured::Key(String::from("main hall"))),
                Err(Misconfigured::Key(long)),
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
