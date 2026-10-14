package org.fyld.rawrecorder;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

/** One CSV file written from one or more threads; lines after close are ignored. */
final class CsvLog {
    private BufferedWriter out;
    private long lines;

    CsvLog(File file, String header) throws IOException {
        out = new BufferedWriter(new FileWriter(file), 1 << 16);
        out.write(header);
        out.write('\n');
    }

    synchronized void line(String text) {
        if (out == null) return;
        try {
            out.write(text);
            out.write('\n');
            lines++;
        } catch (IOException e) {
            close();
        }
    }

    synchronized long lines() {
        return lines;
    }

    synchronized void close() {
        if (out == null) return;
        try {
            out.close();
        } catch (IOException ignored) {
            // the reader reports a file that ends mid-line
        }
        out = null;
    }
}
