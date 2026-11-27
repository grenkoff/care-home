//! Address of a camera, shown only by its host.

use std::fmt;

use retina::client::Credentials;
use url::Url;

/// Camera as a client reaches it.
pub trait Reached {
    /// Returns the location of the stream, without credentials.
    fn location(&self) -> Url;
    /// Returns the credentials the camera asks for, if it asks.
    fn credentials(&self) -> Option<Credentials>;
}

/// Address of a camera that never shows its credentials.
#[derive(Clone, PartialEq, Eq)]
pub struct Address {
    /// Location of the stream on the camera, without credentials.
    location: Url,
    /// User and password the camera asks for.
    credentials: Option<Credentials>,
}

impl Address {
    /// Keeps the location of the stream and the credentials of the camera apart.
    #[must_use]
    pub const fn new(location: Url, credentials: Option<Credentials>) -> Self {
        Self {
            location,
            credentials,
        }
    }
}

impl Reached for Address {
    fn location(&self) -> Url {
        self.location.clone()
    }

    fn credentials(&self) -> Option<Credentials> {
        self.credentials.clone()
    }
}

impl fmt::Display for Address {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let host = self.location.host_str().unwrap_or_default();
        match self.location.port() {
            Some(port) => write!(formatter, "{host}:{port}"),
            None => write!(formatter, "{host}"),
        }
    }
}

impl fmt::Debug for Address {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(self, formatter)
    }
}

#[cfg(test)]
mod tests {
    use retina::client::Credentials;
    use url::Url;

    use super::Address;

    fn keeper() -> Credentials {
        Credentials {
            username: String::from("keeper"),
            password: String::from("secret"),
        }
    }

    #[test]
    fn shows_only_the_host_of_a_camera() {
        let shown = Url::parse("rtsp://keeper:secret@10.0.0.21:554/stream1?token=abc").map(|at| {
            let address = Address::new(at, Some(keeper()));
            (address.to_string(), format!("{address:?}"))
        });
        assert_eq!(
            shown,
            Ok((String::from("10.0.0.21:554"), String::from("10.0.0.21:554")))
        );
    }

    #[test]
    fn shows_a_host_without_a_port() {
        let shown =
            Url::parse("rtsp://camera.home/stream1").map(|at| Address::new(at, None).to_string());
        assert_eq!(shown, Ok(String::from("camera.home")));
    }
}
