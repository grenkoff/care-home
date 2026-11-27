//! Pause before a source connects to its camera again.

use std::time::Duration;

/// Pause that grows after every failed attempt.
pub trait Waiting: Sized {
    /// Returns how long to wait before the next attempt.
    fn length(&self) -> Duration;
    /// Returns the pause after one more failed attempt.
    #[must_use]
    fn longer(self) -> Self;
    /// Returns the pause after an attempt that brought pictures.
    #[must_use]
    fn shortest(self) -> Self;
}

/// Pause that doubles from its first length up to its longest one.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Pause {
    /// Length of the pause after a good attempt.
    first: Duration,
    /// Longest the pause grows.
    longest: Duration,
    /// Length of the pause now.
    length: Duration,
}

impl Pause {
    /// Creates the pause at its first length.
    #[must_use]
    pub const fn new(first: Duration, longest: Duration) -> Self {
        Self {
            first,
            longest,
            length: first,
        }
    }
}

impl Waiting for Pause {
    fn length(&self) -> Duration {
        self.length
    }

    fn longer(self) -> Self {
        Self {
            length: self.length.saturating_mul(2).min(self.longest),
            ..self
        }
    }

    fn shortest(self) -> Self {
        Self {
            length: self.first,
            ..self
        }
    }
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use super::{Pause, Waiting};

    fn pause() -> Pause {
        Pause::new(Duration::from_secs(1), Duration::from_secs(30))
    }

    #[test]
    fn waits_longer_after_each_failed_attempt_up_to_a_limit() {
        let lengths: Vec<u64> = (0..8)
            .scan(pause(), |pause, _| {
                let length = pause.length().as_secs();
                *pause = pause.longer();
                Some(length)
            })
            .collect();
        assert_eq!(lengths, vec![1, 2, 4, 8, 16, 30, 30, 30]);
    }

    #[test]
    fn waits_the_shortest_after_a_session_with_pictures() {
        assert_eq!(
            pause().longer().longer().shortest().length(),
            Duration::from_secs(1)
        );
    }
}
