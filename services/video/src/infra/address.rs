//! Address of a camera, shown only by its host.

use std::fmt;

use url::Url;

/// Address of a camera that never shows its credentials.
#[derive(Clone, PartialEq, Eq)]
pub struct Address {
    /// Location of the stream on the camera.
    location: Url,
}

impl Address {
    /// Wraps the location of the stream on the camera.
    #[must_use]
    pub const fn new(location: Url) -> Self {
        Self { location }
    }
}

impl fmt::Display for Address {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}", self.location)
    }
}

impl fmt::Debug for Address {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}", self.location)
    }
}

#[cfg(test)]
mod tests {
    use url::Url;

    use super::Address;

    #[test]
    fn shows_only_the_host_of_a_camera() {
        let shown = Url::parse("rtsp://keeper:secret@10.0.0.21:554/stream1?token=abc").map(|at| {
            let address = Address::new(at);
            (address.to_string(), format!("{address:?}"))
        });
        assert_eq!(
            shown,
            Ok((String::from("10.0.0.21:554"), String::from("10.0.0.21:554")))
        );
    }

    #[test]
    fn shows_a_host_without_a_port() {
        let shown = Url::parse("rtsp://camera.home/stream1").map(|at| Address::new(at).to_string());
        assert_eq!(shown, Ok(String::from("camera.home")));
    }
}
