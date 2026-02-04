# Test Video Fixtures

Place small test videos here for integration tests.

## Recommended fixtures

- `sample-10s.mp4` - ~500KB, 10 second clip for fast tests
- `sample-30s.mp4` - ~1.5MB, 30 second clip for fuller tests

## Generating test videos

Use ffmpeg to create a test video:

```bash
ffmpeg -f lavfi -i testsrc=duration=10:size=640x360:rate=30 \
       -f lavfi -i sine=frequency=440:duration=10 \
       -c:v libx264 -c:a aac -shortest sample-10s.mp4
```
