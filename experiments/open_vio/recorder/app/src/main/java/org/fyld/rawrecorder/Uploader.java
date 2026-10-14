package org.fyld.rawrecorder;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;

/**
 * Sends a recording folder to experiments/open_vio/host/receive_recording.py, one acknowledged message per file.
 * Wire format of experiment 01's host/protocol.py: 4-byte length + JSON header, 4-byte length + payload.
 */
final class Uploader {
    static final int PORT = 8766;

    interface Progress {
        void update(String text);
    }

    /** Blocks until every file is acknowledged; returns a one-line result. Call from a worker thread. */
    static String send(File recording, String host, Progress progress) {
        List<File> files = new ArrayList<>();
        collect(recording, files);
        long bytes = 0;
        try (Socket socket = new Socket()) {
            socket.connect(new InetSocketAddress(host, PORT), 5000);
            socket.setSoTimeout(15000);
            DataOutputStream out = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream(), 1 << 16));
            DataInputStream in = new DataInputStream(new BufferedInputStream(socket.getInputStream()));
            for (int seq = 0; seq < files.size(); seq++) {
                File file = files.get(seq);
                byte[] data = Files.readAllBytes(file.toPath());
                String path = recording.toURI().relativize(file.toURI()).getPath();
                write(out, new JSONObject().put("type", "file").put("seq", seq).put("recording", recording.getName())
                        .put("path", path).put("size", data.length).put("sha256", sha256(data)), data);
                if (in.readInt() != seq) return "Upload failed: acknowledgement out of order at " + path;
                bytes += data.length;
                if (seq % 30 == 0) progress.update(String.format("Sent %d of %d files (%.0f MB)", seq + 1, files.size(), bytes / 1e6));
            }
            write(out, new JSONObject().put("type", "done").put("recording", recording.getName()).put("files", files.size()), new byte[0]);
            return String.format("Sent %d files (%.0f MB) to %s", files.size(), bytes / 1e6, host);
        } catch (IOException | JSONException | NoSuchAlgorithmException e) {
            return "Upload failed after " + Math.round(bytes / 1e6) + " MB: " + e;
        }
    }

    /** Top-level files (metadata and logs) before the image folder, so a cut upload still leaves them on the computer. */
    private static void collect(File dir, List<File> into) {
        File[] children = dir.listFiles();
        if (children == null) return;
        List<File> folders = new ArrayList<>();
        for (File child : children) {
            if (child.isDirectory()) folders.add(child);
            else into.add(child);
        }
        for (File folder : folders) collect(folder, into);
    }

    private static void write(DataOutputStream out, JSONObject header, byte[] payload) throws IOException {
        byte[] encoded = header.toString().getBytes(StandardCharsets.UTF_8);
        out.writeInt(encoded.length);
        out.write(encoded);
        out.writeInt(payload.length);
        out.write(payload);
        out.flush();
    }

    private static String sha256(byte[] data) throws NoSuchAlgorithmException {
        StringBuilder hex = new StringBuilder();
        for (byte b : MessageDigest.getInstance("SHA-256").digest(data)) hex.append(String.format("%02x", b));
        return hex.toString();
    }
}
