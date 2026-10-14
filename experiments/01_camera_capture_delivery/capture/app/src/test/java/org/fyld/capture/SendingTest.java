package org.fyld.capture;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import org.json.JSONObject;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;

/** The phone-side queue, the matching of camera images to ARCore records, and the windowed sender with resume. */
public class SendingTest {
    @Rule
    public TemporaryFolder tmp = new TemporaryFolder();

    private DiskQueue queueWith(int frames) throws Exception {
        DiskQueue q = DiskQueue.create(tmp.getRoot(), SessionV2Test.SESSION, new JSONObject().put("kind", "walk"));
        for (int i = 0; i < frames; i++) {
            JSONObject h = SessionMessages.message(i % 3 == 2 ? "imu" : "frame", SessionV2Test.SESSION);
            q.add(h, new byte[1000 + i]);
        }
        return q;
    }

    @Test
    public void queueNumbersMessagesAndDeletesThemOnlyWhenAcknowledged() throws Exception {
        DiskQueue q = queueWith(6);
        assertEquals(6, q.nextN());
        assertEquals(4, q.pendingFrames());
        assertNotNull(q.file(5));
        assertNull(q.file(6));
        q.ackThrough(2);
        assertNull(q.file(2));
        assertNotNull(q.file(3));
        assertEquals(2, q.pendingFrames());  // frames 3 and 4; 2 and 5 are motion-sensor batches
        assertEquals(2, q.ackedFrames());
        long end = q.end(SessionMessages.end(SessionV2Test.SESSION, "stop", new JSONObject(), new JSONObject()));
        assertEquals(6, end);
        assertTrue(q.ended());
        assertEquals(6, q.endN());
        JSONObject stored = SessionMessages.read(new DataInputStream(new java.io.FileInputStream(q.file(4))));
        assertEquals(4, stored.getLong("n"));
    }

    @Test
    public void reopenedQueueContinuesNumberingAfterEverythingWasAcknowledged() throws Exception {
        DiskQueue q = queueWith(3);
        q.ackThrough(2);
        File dir = q.dir();
        DiskQueue.forget(dir);
        DiskQueue again = DiskQueue.open(dir);
        assertEquals(3, again.nextN());
        assertEquals(0, again.pendingFrames());
        assertFalse(again.ended());
        assertEquals("walk", again.info().getString("kind"));
    }

    @Test
    public void failedAckCheckpointKeepsTheLastMessageForRestart() throws Exception {
        DiskQueue q = queueWith(1);
        assertTrue(new File(q.dir(), "through.tmp").mkdir());
        assertThrows(java.io.IOException.class, () -> q.ackThrough(0));
        assertTrue(new File(q.dir(), "0000000000-f.msg").exists());
        DiskQueue.forget(q.dir());
        assertEquals(1, DiskQueue.open(q.dir()).nextN());
    }

    @Test
    public void reopenedQueueFindsEndWrittenBeforeItsMarker() throws Exception {
        DiskQueue q = queueWith(1);
        long end = q.add(SessionMessages.end(q.id(), "stop", new JSONObject(), new JSONObject()), new byte[0]);
        DiskQueue.forget(q.dir());
        DiskQueue reopened = DiskQueue.open(q.dir());
        assertTrue(reopened.ended());
        assertEquals(end, reopened.endN());
        assertTrue(new File(q.dir(), "end").exists());
    }

    @Test
    public void firstTrackingFrameCreatesAnAnchorWithoutTimestampOverflow() {
        FrameCapture capture = new FrameCapture(null, false);
        assertTrue(capture.anchorDue(5_000_100_000_000L));
        assertTrue(capture.anchorDue(0));
    }

    @Test
    public void assemblerJoinsOutOfOrderPartsAndEmitsInImageOrder() throws Exception {
        FrameAssembler a = new FrameAssembler(true);
        ArcoreRecord early = new ArcoreRecord();
        a.addArcore(200, early);  // ARCore can report an image before the app's reader delivers it
        assertTrue(a.addImage(100, a.buffer(6), 2, 1, 7, 0));
        assertTrue(a.addImage(200, a.buffer(6), 2, 1, 8, 1));
        a.addCamera(200, new JSONObject());
        assertTrue("frame 100 is incomplete and blocks 200", a.ready(10_000_000L, false).isEmpty());
        a.addCamera(100, new JSONObject());
        a.addArcore(100, new ArcoreRecord());
        List<FrameAssembler.Pending> out = a.ready(10_000_000L, false);
        assertEquals(2, out.size());
        assertEquals(100, out.get(0).t);
        assertTrue(out.get(1).arcore == early);
        a.addArcore(100, new ArcoreRecord());  // too late: its frame has gone
        assertEquals(1, a.lateArcore());
    }

    @Test
    public void assemblerGivesUpWaitingAfterTheLimitAndDropsWhenFull() {
        FrameAssembler a = new FrameAssembler(true);
        a.addImage(100, a.buffer(6), 2, 1, 0, 0);
        assertTrue(a.ready(FrameAssembler.WAIT_NS - 1, false).isEmpty());
        FrameAssembler.Pending p = a.ready(FrameAssembler.WAIT_NS, false).get(0);
        assertNull(p.arcore);
        assertNull(p.camera);
        for (int i = 0; i < FrameAssembler.MAX_PENDING; i++) assertTrue(a.addImage(1000 + i, a.buffer(6), 2, 1, 0, 0));
        assertFalse(a.addImage(5000, a.buffer(6), 2, 1, 0, 0));
        assertEquals(1, a.dropped());
        assertEquals(FrameAssembler.MAX_PENDING, a.ready(0, true).size());
    }

    /**
     * A fake PC that stores messages 0..5 on its first connection, drops the connection without acknowledging 4 and 5,
     * and on the second connection says it holds 0..5; the phone must resend from 6 and finish with the end message.
     */
    @Test
    public void senderResumesAfterADroppedConnectionWithoutLossOrRepeats() throws Exception {
        DiskQueue q = queueWith(10);
        q.end(SessionMessages.end(SessionV2Test.SESSION, "stop", new JSONObject(), new JSONObject()));
        List<Long> stored = new ArrayList<>();
        List<Long> firstOnConnection = new ArrayList<>();
        AtomicReference<Throwable> failure = new AtomicReference<>();
        try (ServerSocket server = new ServerSocket(0)) {
            Thread host = new Thread(() -> {
                try {
                    for (int connection = 0; connection < 2; connection++) {
                        try (Socket s = server.accept()) {
                            DataInputStream in = new DataInputStream(new BufferedInputStream(s.getInputStream()));
                            DataOutputStream out = new DataOutputStream(new BufferedOutputStream(s.getOutputStream()));
                            JSONObject hello = SessionMessages.read(in);
                            assertEquals("hello", hello.getString("type"));
                            long through = stored.isEmpty() ? -1 : stored.get(stored.size() - 1);
                            SessionMessages.write(out, ack(through), new byte[0]);
                            boolean first = true;
                            while (true) {
                                JSONObject m = SessionMessages.read(in);
                                long n = m.getLong("n");
                                if (first) firstOnConnection.add(n);
                                first = false;
                                stored.add(n);
                                if (connection == 0 && n == 5) break;  // drop without acknowledging 4 and 5
                                if (connection == 0 && n >= 4) continue;
                                SessionMessages.write(out, ack(n), new byte[0]);
                                if (m.getString("type").equals("end")) return;
                            }
                        }
                    }
                } catch (Throwable e) {
                    failure.set(e);
                }
            });
            host.start();
            Uploader uploader = new Uploader(tmp.getRoot(), "127.0.0.1", server.getLocalPort(), text -> { });
            uploader.drainAll();
            host.join(10000);
        }
        if (failure.get() != null) throw new AssertionError(failure.get());
        List<Long> expected = new ArrayList<>();
        for (long n = 0; n <= 10; n++) expected.add(n);
        assertEquals(expected, stored);
        assertEquals(List.of(0L, 6L), firstOnConnection);
        assertFalse("a delivered session is deleted from the phone", q.dir().exists());
        assertEquals(7, q.ackedFrames());
    }

    /** A PC that answers hello and then stops reading: the blocked write must be abandoned and the session resent. */
    @Test
    public void senderAbandonsAConnectionThatStopsMoving() throws Exception {
        DiskQueue q = DiskQueue.create(tmp.getRoot(), SessionV2Test.SESSION, new JSONObject().put("kind", "walk"));
        for (int i = 0; i < 80; i++) q.add(SessionMessages.message("frame", SessionV2Test.SESSION), new byte[300_000]);
        q.end(SessionMessages.end(SessionV2Test.SESSION, "stop", new JSONObject(), new JSONObject()));
        List<Long> stored = new ArrayList<>();
        AtomicReference<Throwable> failure = new AtomicReference<>();
        try (ServerSocket server = new ServerSocket(0)) {
            Thread host = new Thread(() -> {
                try (Socket silent = server.accept()) {
                    SessionMessages.read(new DataInputStream(new BufferedInputStream(silent.getInputStream())));
                    SessionMessages.write(new DataOutputStream(silent.getOutputStream()), ack(-1), new byte[0]);
                    try (Socket s = server.accept()) {  // the phone gives up on the silent connection and comes back
                        DataInputStream in = new DataInputStream(new BufferedInputStream(s.getInputStream()));
                        DataOutputStream out = new DataOutputStream(new BufferedOutputStream(s.getOutputStream()));
                        SessionMessages.read(in);
                        SessionMessages.write(out, ack(-1), new byte[0]);
                        while (true) {
                            JSONObject m = SessionMessages.read(in);
                            stored.add(m.getLong("n"));
                            SessionMessages.write(out, ack(m.getLong("n")), new byte[0]);
                            if (m.getString("type").equals("end")) return;
                        }
                    }
                } catch (Throwable e) {
                    failure.set(e);
                }
            });
            host.start();
            Uploader uploader = new Uploader(tmp.getRoot(), "127.0.0.1", server.getLocalPort(), text -> { });
            uploader.timeoutMs = 1000;
            Thread phone = new Thread(uploader::drainAll);
            phone.setDaemon(true);
            phone.start();
            phone.join(20000);
            assertFalse("the sender is still stuck on the silent connection", phone.isAlive());
            host.join(5000);
        }
        if (failure.get() != null) throw new AssertionError(failure.get());
        assertEquals(81, stored.size());
        assertEquals(80L, (long) stored.get(80));
        assertFalse(q.dir().exists());
    }

    @Test
    public void refusedSessionIsKeptAndSkipped() throws Exception {
        DiskQueue q = queueWith(2);
        q.end(SessionMessages.end(SessionV2Test.SESSION, "stop", new JSONObject(), new JSONObject()));
        try (ServerSocket server = new ServerSocket(0)) {
            Thread host = new Thread(() -> {
                try (Socket s = server.accept()) {
                    SessionMessages.read(new DataInputStream(new BufferedInputStream(s.getInputStream())));
                    DataOutputStream out = new DataOutputStream(new BufferedOutputStream(s.getOutputStream()));
                    SessionMessages.write(out, new JSONObject().put("type", "error").put("message", "bad frame"), new byte[0]);
                } catch (Exception ignored) {
                    // the assertions below report the outcome
                }
            });
            host.start();
            List<String> said = new ArrayList<>();
            new Uploader(tmp.getRoot(), "127.0.0.1", server.getLocalPort(), said::add).drainAll();
            host.join(5000);
            assertTrue(q.refused());
            assertTrue(q.dir().exists());
            assertTrue(String.join("\n", said).contains("bad frame"));
            assertTrue(DiskQueue.sessions(tmp.getRoot()).isEmpty());
        }
    }

    @Test
    public void wireFormatMatchesTheHostFraming() throws Exception {
        byte[] bytes = SessionMessages.encode(new JSONObject().put("type", "ack"), new byte[]{9});
        assertArrayEquals(new byte[]{0, 0, 0, 14}, java.util.Arrays.copyOfRange(bytes, 0, 4));
        assertArrayEquals(new byte[]{0, 0, 0, 1, 9}, java.util.Arrays.copyOfRange(bytes, bytes.length - 5, bytes.length));
    }

    private static JSONObject ack(long through) throws Exception {
        return new JSONObject().put("type", "ack").put("session", SessionV2Test.SESSION).put("through", through);
    }
}
