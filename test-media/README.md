# Test Media Directory

This directory is for working with test videos during development.

**This directory is gitignored** - files here won't be committed.

## Usage

Place your test videos here when working on vcut features:

```bash
# Copy a video for testing
cp ~/Videos/my-test.mp4 test-media/

# Transcribe it
vcut transcribe test-media/my-test.mp4

# Edit and render
vcut render test-media/my-test.txt
```

## Generating test videos

```bash
# 10-second test video with audio
ffmpeg -f lavfi -i testsrc=duration=10:size=640x360:rate=30 \
       -f lavfi -i sine=frequency=440:duration=10 \
       -c:v libx264 -c:a aac -shortest test-media/sample-10s.mp4
```
