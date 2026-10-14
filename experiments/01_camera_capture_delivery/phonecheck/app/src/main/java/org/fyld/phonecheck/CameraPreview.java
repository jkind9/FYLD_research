package org.fyld.phonecheck;

import android.opengl.GLES11Ext;
import android.opengl.GLES20;

import com.google.ar.core.Coordinates2d;
import com.google.ar.core.Frame;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;

/** Draws ARCore's camera image full screen: one textured quad, mapped to the display by ARCore. GL thread only. */
final class CameraPreview {
    private static final String VERTEX =
            "attribute vec4 a_Position; attribute vec2 a_TexCoord; varying vec2 v_TexCoord;"
            + "void main() { gl_Position = a_Position; v_TexCoord = a_TexCoord; }";
    private static final String FRAGMENT =
            "#extension GL_OES_EGL_image_external : require\n"
            + "precision mediump float; varying vec2 v_TexCoord; uniform samplerExternalOES u_Texture;"
            + "void main() { gl_FragColor = texture2D(u_Texture, v_TexCoord); }";
    private static final float[] QUAD = {-1f, -1f, +1f, -1f, -1f, +1f, +1f, +1f};

    private final FloatBuffer quad = buffer(QUAD.length);
    private final FloatBuffer texCoords = buffer(QUAD.length);
    private int program, position, texCoord, texture;

    /** Creates the camera texture and the shader; returns the texture name to give to the ARCore session. */
    int create() {
        int[] ids = new int[1];
        GLES20.glGenTextures(1, ids, 0);
        texture = ids[0];
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, texture);
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR);
        program = GLES20.glCreateProgram();
        GLES20.glAttachShader(program, shader(GLES20.GL_VERTEX_SHADER, VERTEX));
        GLES20.glAttachShader(program, shader(GLES20.GL_FRAGMENT_SHADER, FRAGMENT));
        GLES20.glLinkProgram(program);
        position = GLES20.glGetAttribLocation(program, "a_Position");
        texCoord = GLES20.glGetAttribLocation(program, "a_TexCoord");
        quad.put(QUAD).position(0);
        return texture;
    }

    void draw(Frame frame) {
        if (frame.hasDisplayGeometryChanged()) {
            frame.transformCoordinates2d(Coordinates2d.OPENGL_NORMALIZED_DEVICE_COORDINATES, quad,
                    Coordinates2d.TEXTURE_NORMALIZED, texCoords);
        }
        if (frame.getTimestamp() == 0) return;  // no camera image yet
        GLES20.glDisable(GLES20.GL_DEPTH_TEST);
        GLES20.glUseProgram(program);
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, texture);
        quad.position(0);
        texCoords.position(0);
        GLES20.glVertexAttribPointer(position, 2, GLES20.GL_FLOAT, false, 0, quad);
        GLES20.glVertexAttribPointer(texCoord, 2, GLES20.GL_FLOAT, false, 0, texCoords);
        GLES20.glEnableVertexAttribArray(position);
        GLES20.glEnableVertexAttribArray(texCoord);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);
        GLES20.glDisableVertexAttribArray(position);
        GLES20.glDisableVertexAttribArray(texCoord);
    }

    private static int shader(int type, String source) {
        int id = GLES20.glCreateShader(type);
        GLES20.glShaderSource(id, source);
        GLES20.glCompileShader(id);
        return id;
    }

    private static FloatBuffer buffer(int floats) {
        return ByteBuffer.allocateDirect(floats * 4).order(ByteOrder.nativeOrder()).asFloatBuffer();
    }
}
