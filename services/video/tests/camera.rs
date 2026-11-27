//! Camera source against a fake RTSP camera that plays the demo pattern.

use std::collections::BTreeMap;
use std::sync::{Arc, RwLock};
use std::time::Duration;

use retina::client::Credentials;
use tokio::io::{AsyncBufReadExt, AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::mpsc::{UnboundedReceiver, UnboundedSender, unbounded_channel};
use url::Url;
use video::domain::frames::{Frame, Framed};
use video::domain::nal::{AnnexB, Nal, Unit, Units};
use video::domain::pause::Pause;
use video::domain::streams::{Recorded, Restarted, Streams, Unrecorded, Watched};
use video::domain::window::{Growing, Live, Window};
use video::infra::address::Address;
use video::infra::camera::Camera;
use video::infra::demo::{PATTERN_RATE, Pattern};
use video::infra::lineup::{Lineup, Wired};
use video::infra::listing::{Configured, Listing};
use video::infra::sources::Playing;

/// The committed test pattern the fake camera plays.
const PATTERN: &[u8] = include_bytes!("../demo/pattern.h264");

/// Ticks of the RTP clock between two pictures of the pattern.
const TICKS: u32 = 6_000;

/// Pictures in one loop of the pattern.
const LOOP: usize = 60;

/// Authorization the fake camera accepts: `keeper` with the password `secret`.
const ACCEPTED: &str = "Basic a2VlcGVyOnNlY3JldA==";

/// Payload type of the H.264 video in the description of the fake camera.
const PAYLOAD: u8 = 96;

/// Status, headers and body of the answer to a request without the accepted authorization.
const UNAUTHORIZED: [&str; 3] = [
    "401 Unauthorized",
    "WWW-Authenticate: Basic realm=\"camera\"\r\n",
    "",
];

/// Status, headers and body of the description of the stream.
const DESCRIBED: [&str; 3] = [
    "200 OK",
    "Content-Type: application/sdp\r\n",
    "v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=pattern\r\nc=IN IP4 0.0.0.0\r\nt=0 0\r\n\
     m=video 0 RTP/AVP 96\r\na=rtpmap:96 H264/90000\r\na=fmtp:96 packetization-mode=1\r\n\
     a=control:trackID=1\r\n",
];

/// Status, headers and body of a description that offers a JPEG video before the H.264 one.
const MIXED: [&str; 3] = [
    "200 OK",
    "Content-Type: application/sdp\r\n",
    "v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=pattern\r\nc=IN IP4 0.0.0.0\r\nt=0 0\r\n\
     m=video 0 RTP/AVP 26\r\na=control:trackID=0\r\n\
     m=video 0 RTP/AVP 96\r\na=rtpmap:96 H264/90000\r\na=fmtp:96 packetization-mode=1\r\n\
     a=control:trackID=1\r\n",
];

/// Status, headers and body of the answer to SETUP: RTP interleaved in the connection.
const SET_UP: [&str; 3] = [
    "200 OK",
    "Transport: RTP/AVP/TCP;unicast;interleaved=0-1\r\nSession: 4F2A;timeout=60\r\n",
    "",
];

/// Status, headers and body of the answer to PLAY.
const PLAYING: [&str; 3] = ["200 OK", "Session: 4F2A\r\n", ""];

/// Status, headers and body of the answer to any other request.
const OFFERED: [&str; 3] = [
    "200 OK",
    "Public: OPTIONS, DESCRIBE, SETUP, PLAY, TEARDOWN, GET_PARAMETER\r\n",
    "",
];

/// Longest a test waits for the source.
const PATIENCE: Duration = Duration::from_secs(3);

/// What the fake camera does after it played the pattern.
#[derive(Debug, Clone, Copy)]
enum Ending {
    /// Closes the connection.
    HangUp,
    /// Keeps the connection open and sends nothing more.
    Silence,
    /// Keeps sending RTCP sender reports and no pictures.
    Reports,
}

/// What the source did to the stream.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Event {
    /// A picture of the duration went into the stream.
    Recorded(u32),
    /// The stream started anew.
    Restarted,
}

/// Streams that tell the test about every change.
struct Watcher {
    /// Streams that keep the pictures.
    streams: Streams,
    /// Channel of the changes.
    events: UnboundedSender<Event>,
}

impl Recorded for Watcher {
    fn record(&self, stream: &str, frame: &Frame, duration: u32) -> Result<(), Unrecorded> {
        self.streams.record(stream, frame, duration)?;
        self.events
            .send(Event::Recorded(duration))
            .map_err(|_| Unrecorded::Unknown(stream.to_owned()))
    }
}

impl Restarted for Watcher {
    fn restart(&self, stream: &str) -> Result<(), Unrecorded> {
        self.streams.restart(stream)?;
        self.events
            .send(Event::Restarted)
            .map_err(|_| Unrecorded::Unknown(stream.to_owned()))
    }
}

/// Fake camera that serves the pattern over RTSP with RTP interleaved in TCP.
struct Fake {
    /// Socket the camera listens on.
    listener: TcpListener,
    /// Loops of the pattern it plays in one session.
    loops: usize,
    /// What it does after it played them.
    ending: Ending,
    /// Answer to DESCRIBE.
    described: [&'static str; 3],
    /// Channel that hears of every connection.
    attempts: UnboundedSender<()>,
}

impl Fake {
    /// Answers every connection until the test ends.
    async fn serve(self) {
        while let Ok((connection, _)) = self.listener.accept().await {
            if self.attempts.send(()).is_err() {
                break;
            }
            let visit = Visit {
                reader: BufReader::new(connection),
                loops: self.loops,
                ending: self.ending,
                described: self.described,
            };
            tokio::spawn(visit.answer());
        }
    }
}

/// One connection of a client to the fake camera.
struct Visit {
    /// Connection with the client.
    reader: BufReader<TcpStream>,
    /// Loops of the pattern to play.
    loops: usize,
    /// What to do after playing them.
    ending: Ending,
    /// Answer to DESCRIBE.
    described: [&'static str; 3],
}

impl Visit {
    /// Answers the requests of the client and plays the pattern after PLAY.
    async fn answer(mut self) {
        while let Some((method, sequence, authorization)) = self.request().await {
            let reply = match method.as_str() {
                "DESCRIBE" if authorization.as_deref() != Some(ACCEPTED) => UNAUTHORIZED,
                "DESCRIBE" => self.described,
                "SETUP" => SET_UP,
                "PLAY" => PLAYING,
                _ => OFFERED,
            };
            let answered = self.respond(&sequence, reply).await;
            if !answered || (method == "PLAY" && !self.played().await) {
                return;
            }
        }
    }

    /// Reads one request: its method, its sequence number and its authorization.
    async fn request(&mut self) -> Option<(String, String, Option<String>)> {
        let mut line = String::new();
        self.reader
            .read_line(&mut line)
            .await
            .ok()
            .filter(|read| *read > 0)?;
        let method = line.split_whitespace().next()?.to_owned();
        let mut sequence = String::new();
        let mut authorization = None;
        loop {
            let mut header = String::new();
            self.reader
                .read_line(&mut header)
                .await
                .ok()
                .filter(|read| *read > 0)?;
            let header = header.trim_end();
            if header.is_empty() {
                return Some((method, sequence, authorization));
            }
            if let Some((name, value)) = header.split_once(':') {
                match name.trim().to_ascii_lowercase().as_str() {
                    "cseq" => value.trim().clone_into(&mut sequence),
                    "authorization" => authorization = Some(value.trim().to_owned()),
                    _ => {}
                }
            }
        }
    }

    /// Sends a response and tells whether it went out.
    async fn respond(&mut self, sequence: &str, reply: [&str; 3]) -> bool {
        let [status, headers, body] = reply;
        let address = self
            .reader
            .get_ref()
            .local_addr()
            .map(|at| at.to_string())
            .unwrap_or_default();
        let response = format!(
            "RTSP/1.0 {status}\r\nCSeq: {sequence}\r\nContent-Base: rtsp://{address}/pattern/\r\n\
             {headers}Content-Length: {}\r\n\r\n{body}",
            body.len()
        );
        self.reader
            .get_mut()
            .write_all(response.as_bytes())
            .await
            .is_ok()
    }

    /// Plays the pattern, then ends as told, and tells whether the connection stays.
    async fn played(&mut self) -> bool {
        let pictures = pictures();
        let mut sequence: u16 = 0;
        for (index, picture) in pictures.iter().cycle().take(self.loops * LOOP).enumerate() {
            let time = u32::try_from(index).unwrap_or_default() * TICKS;
            for (part, unit) in picture.iter().enumerate() {
                let marker = if part + 1 == picture.len() { 0x80 } else { 0 };
                let mut packet = vec![0x80, marker | PAYLOAD];
                packet.extend(sequence.to_be_bytes());
                packet.extend(time.to_be_bytes());
                packet.extend(0x1234_5678_u32.to_be_bytes());
                packet.extend(unit.bytes());
                let length = u16::try_from(packet.len()).unwrap_or_default();
                let framed: Vec<u8> = [b'$', 0]
                    .into_iter()
                    .chain(length.to_be_bytes())
                    .chain(packet)
                    .collect();
                if self.reader.get_mut().write_all(&framed).await.is_err() {
                    return false;
                }
                sequence = sequence.wrapping_add(1);
            }
        }
        self.ended().await
    }

    /// Ends the session as told once the pattern was played, and tells whether the connection stays.
    async fn ended(&mut self) -> bool {
        match self.ending {
            Ending::HangUp => false,
            Ending::Reports => {
                let mut reports = tokio::time::interval(Duration::from_millis(50));
                let report: Vec<u8> = [b'$', 1, 0, 28, 0x80, 200, 0, 6]
                    .into_iter()
                    .chain(0x1234_5678_u32.to_be_bytes())
                    .chain([0; 20])
                    .collect();
                loop {
                    reports.tick().await;
                    if self.reader.get_mut().write_all(&report).await.is_err() {
                        return false;
                    }
                }
            }
            Ending::Silence => {
                let mut sink = Vec::new();
                let _ = self.reader.read_to_end(&mut sink).await;
                false
            }
        }
    }
}

/// Units of the pattern grouped into pictures.
fn pictures() -> Vec<Vec<Unit>> {
    AnnexB::new(PATTERN)
        .units()
        .into_iter()
        .fold(Vec::<Vec<Unit>>::new(), |mut pictures, unit| {
            let started = pictures
                .last()
                .is_some_and(|picture| picture.iter().any(Nal::sliced));
            if pictures.is_empty() || (started && (unit.opening() || !unit.sliced())) {
                pictures.push(vec![unit]);
            } else if let Some(picture) = pictures.last_mut() {
                picture.push(unit);
            }
            pictures
        })
}

/// Starts a fake camera that describes one H.264 video.
async fn camera(
    loops: usize,
    ending: Ending,
) -> Result<(Url, UnboundedReceiver<()>), Box<dyn std::error::Error>> {
    offering(loops, ending, DESCRIBED).await
}

/// Starts a fake camera and returns its address and the channel of its connections.
async fn offering(
    loops: usize,
    ending: Ending,
    described: [&'static str; 3],
) -> Result<(Url, UnboundedReceiver<()>), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind("127.0.0.1:0").await?;
    let at = Url::parse(&format!("rtsp://{}/pattern/", listener.local_addr()?))?;
    let (attempts, heard) = unbounded_channel();
    tokio::spawn(
        Fake {
            listener,
            loops,
            ending,
            described,
            attempts,
        }
        .serve(),
    );
    Ok((at, heard))
}

/// Credentials of the keeper with the password.
fn keeper(password: &str) -> Credentials {
    Credentials {
        username: String::from("keeper"),
        password: password.to_owned(),
    }
}

/// Streams with the keys and the channel of their changes.
fn watched(keys: &[&str]) -> (Arc<Watcher>, UnboundedReceiver<Event>) {
    let (events, heard) = unbounded_channel();
    let watcher = Watcher {
        streams: Streams::new(
            keys.iter()
                .map(|key| ((*key).to_owned(), RwLock::new(Window::new(5, 180_000))))
                .collect::<BTreeMap<_, _>>(),
        ),
        events,
    };
    (Arc::new(watcher), heard)
}

/// Source of the stream from the camera with the password, short pauses and the given silence.
fn source(at: Url, password: &str, silence: Duration, streams: &Arc<Watcher>) -> Camera<Watcher> {
    Camera::new(
        "hall",
        Address::new(at, Some(keeper(password))),
        (
            silence,
            Pause::new(Duration::from_millis(10), Duration::from_millis(40)),
        ),
        Arc::clone(streams),
    )
}

/// Plays the source until the stream got the count of pictures, and returns how many it got.
async fn filled(
    source: &(impl Playing + Sync),
    heard: &mut UnboundedReceiver<Event>,
    count: usize,
) -> Result<usize, &'static str> {
    tokio::select! {
        waited = tokio::time::timeout(PATIENCE, until(heard, |events| events.len() >= count)) => {
            waited.map(|events| events.len()).map_err(|_| "the stream was not filled in time")
        }
        _ = source.play() => Err("the source stopped"),
    }
}

/// Collects the events until they pass the test.
async fn until(
    heard: &mut UnboundedReceiver<Event>,
    passed: impl Fn(&[Event]) -> bool,
) -> Vec<Event> {
    let mut events = Vec::new();
    while !passed(&events)
        && let Some(event) = heard.recv().await
    {
        events.push(event);
    }
    events
}

/// Tells whether the stream started anew and got a picture after that.
fn refilled(events: &[Event]) -> bool {
    events
        .iter()
        .position(|event| *event == Event::Restarted)
        .is_some_and(|restart| events[restart..].contains(&Event::Recorded(TICKS)))
}

#[tokio::test]
async fn fills_a_stream_from_a_camera() {
    let (at, _attempts) = camera(3, Ending::Silence).await.unwrap();
    let (streams, mut heard) = watched(&["hall"]);
    let hall = source(at, "secret", PATIENCE, &streams);
    let recorded = 3 * LOOP - 1;
    let events = tokio::select! {
        waited = tokio::time::timeout(PATIENCE, until(&mut heard, |events| events.len() >= recorded)) => {
            waited.map_err(|_| "the stream was not filled in time")
        }
        _ = hall.play() => Err("the source stopped"),
    };
    let expected = Pattern
        .frames()
        .iter()
        .cycle()
        .take(recorded)
        .try_fold(Window::new(5, 180_000), |window, frame| {
            window.with(frame, TICKS)
        })
        .unwrap();
    assert_eq!(
        (
            events,
            streams.streams.init("hall"),
            streams.streams.playlist("hall")
        ),
        (
            Ok(vec![Event::Recorded(TICKS); recorded]),
            Ok(expected.init().unwrap()),
            Ok(expected.playlist().unwrap())
        )
    );
}

/// Waits until the source filled the stream again after the camera was lost.
async fn reconnected(ending: Ending, silence: Duration) -> Result<(), &'static str> {
    let (at, mut attempts) = camera(1, ending)
        .await
        .map_err(|_| "the camera did not start")?;
    let (streams, mut heard) = watched(&["hall"]);
    let hall = source(at, "secret", silence, &streams);
    tokio::select! {
        waited = tokio::time::timeout(PATIENCE, async {
            until(&mut heard, refilled).await;
            (attempts.recv().await, attempts.recv().await)
        }) => match waited {
            Ok((Some(()), Some(()))) => Ok(()),
            Ok(_) => Err("the camera did not hear a second connection"),
            Err(_) => Err("the stream was not filled again in time"),
        },
        _ = hall.play() => Err("the source stopped"),
    }
}

#[tokio::test]
async fn connects_again_when_the_camera_hangs_up() {
    assert_eq!(reconnected(Ending::HangUp, PATIENCE).await, Ok(()));
}

#[tokio::test]
async fn connects_again_when_the_camera_falls_silent() {
    assert_eq!(
        reconnected(Ending::Silence, Duration::from_millis(300)).await,
        Ok(())
    );
}

#[tokio::test]
async fn connects_again_when_the_camera_sends_reports_without_pictures() {
    assert_eq!(
        reconnected(Ending::Reports, Duration::from_millis(300)).await,
        Ok(())
    );
}

#[tokio::test]
async fn keeps_other_streams_going_when_a_camera_refuses_the_password() {
    let (hall_at, _hall_attempts) = camera(1, Ending::Silence).await.unwrap();
    let (porch_at, mut porch_attempts) = camera(1, Ending::Silence).await.unwrap();
    let (streams, mut heard) = watched(&["hall"]);
    let hall = source(hall_at, "secret", PATIENCE, &streams);
    let porch = source(porch_at, "wrong", PATIENCE, &streams);
    let outcome = tokio::select! {
        waited = tokio::time::timeout(PATIENCE, async {
            let events = until(&mut heard, |events| events.len() >= LOOP - 1).await;
            let mut tries = 0;
            while tries < 3 && porch_attempts.recv().await.is_some() {
                tries += 1;
            }
            (events.len(), tries)
        }) => waited.map_err(|_| "the streams did not go on in time"),
        _ = hall.play() => Err("the source of the hall stopped"),
        _ = porch.play() => Err("the source of the porch stopped"),
    };
    assert_eq!(outcome, Ok((LOOP - 1, 3)));
}

/// Plays the first stream the setting lists until it got a loop of the pattern.
async fn listed(setting: String) -> Result<usize, &'static str> {
    let listed = Listing::new(setting)
        .streams()
        .map_err(|_| "the setting was refused")?;
    let lineup = Lineup::new(
        listed,
        (5, 180_000),
        (Pattern.frames().into(), PATTERN_RATE),
        (
            PATIENCE,
            Pause::new(Duration::from_millis(10), Duration::from_millis(40)),
        ),
    );
    let (events, mut heard) = unbounded_channel();
    let watcher = Arc::new(Watcher {
        streams: lineup.streams(),
        events,
    });
    let sources = lineup.sources(&watcher);
    let first = sources.first().ok_or("the setting lists no stream")?;
    filled(first, &mut heard, LOOP - 1).await
}

#[tokio::test]
async fn plays_a_camera_the_setting_lists() {
    let (at, _attempts) = camera(1, Ending::Silence).await.unwrap();
    let setting = format!(
        "porch=rtsp://keeper:%73ecret@{}:{}{}",
        at.host_str().unwrap(),
        at.port().unwrap(),
        at.path()
    );
    assert_eq!(listed(setting).await, Ok(LOOP - 1));
}

#[tokio::test]
async fn takes_the_h264_video_of_a_camera_that_offers_more_streams() {
    let (at, _attempts) = offering(1, Ending::Silence, MIXED).await.unwrap();
    let (streams, mut heard) = watched(&["hall"]);
    let hall = source(at, "secret", PATIENCE, &streams);
    assert_eq!(filled(&hall, &mut heard, LOOP - 1).await, Ok(LOOP - 1));
}
