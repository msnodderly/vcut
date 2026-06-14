# Agent usage example 
```
$ claude
╭─── Claude Code v2.1.177 ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                    │ Tips for getting started                                                       │
│                  Welcome back mds!                 │ Run /init to create a CLAUDE.md file with instructions for Claude              │
│                                                    │ ────────────────────────────────────────────────────────────────────────────── │
│                       ▐▛███▜▌                      │ What's new                                                                     │
│                      ▝▜█████▛▘                     │ Session titles are now generated in the language of your conversation (set th… │
│                        ▘▘ ▝▝                       │ Added `footerLinksRegexes` setting for regex-matched link badges in the foote… │
│     Sonnet 4.6 with high effort · Claude Pro ·     │ Improved Bedrock credential caching: credentials from `awsCredentialExport` a… │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

❯ /model
  ⎿  Set model to Sonnet 4.6 and saved as your default for new sessions

❯ use uvx vcut --help and yt-dlp to download https://www.youtube.com/watch?v=G1xqTjoihfo and create a snippet of the section where
  theo introduces patch.md

⏺ I'll check the vcut help and download the video in parallel.

⏺ Bash(uvx vcut --help 2>&1)
  ⎿  usage: vcut [-h] {transcribe,t,render,r,edit,e} ...

     Edit video by editing its transcript.
     … +78 lines (ctrl+o to expand)
  ⎿  Allowed by auto mode classifier

⏺ Bash(yt-dlp --get-title --get-duration "https://www.youtube.com/watch?v=G1xqTjoihfo" 2>&1)
  ⎿  WARNING: Your yt-dlp version (2026.01.31) is older than 90 days!
              It is strongly recommended to always use the latest version.
              You installed yt-dlp with pip or using the wheel from PyPi; Use that to update.
     … +13 lines (ctrl+o to expand)
  ⎿  Allowed by auto mode classifier

⏺ The video is "A letter to tech CEOs" (39:43). Let me download it and transcribe it.

⏺ Bash(yt-dlp --no-update -o "/tmp/theo-letter.%(ext)s" "https://www.youtube.com/watch?v=G1xqTjoihfo" 2>&1)
  ⎿  [youtube] Extracting URL: https://www.youtube.com/watch?v=G1xqTjoihfo
     [youtube] G1xqTjoihfo: Downloading webpage
     [youtube] G1xqTjoihfo: Downloading android vr player API JSON
     … +56 lines (ctrl+o to expand)
  ⎿  (timeout 5m)
  ⎿  Allowed by auto mode classifier

⏺ Video downloaded. Now transcribing it.

⏺ Bash(uvx vcut transcribe "/tmp/theo-letter.mp4" -o /tmp/theo-letter.vcut.txt -m balanced -l en -c 2 --force 2>&1)
  ⎿  Extracting audio...
       Transcribing... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:03:57
     Transcript saved: /tmp/theo-letter.vcut.txt
     Next: vcut edit /tmp/theo-letter.mp4  (or: vcut render /tmp/theo-letter.mp4)
  ⎿  (timeout 10m)
  ⎿  Allowed by auto mode classifier

⏺ Transcription done. Now searching for "patch.md" mentions.

  Searched for 1 pattern (ctrl+o to expand)

⏺ Found the intro at line 894. Let me see the surrounding context to pick good start/end timestamps.

⏺ Bash(sed -n '885,950p' /tmp/theo-letter.vcut.txt)
  ⎿  [00:32:29.240 -> 00:32:31.340] | I've been thinking about these a lot in particular
     [00:32:31.820 -> 00:32:34.060] | the soul MD the idea of
     [00:32:34.060 -> 00:32:36.240] | a piece of software that was designed to have
     … +63 lines (ctrl+o to expand)
  ⎿  Allowed by auto mode classifier

⏺ Bash(sed -n '950,980p' /tmp/theo-letter.vcut.txt)
  ⎿  [00:34:50.640 -> 00:34:52.740] | would clone the latest code see
     [00:34:52.740 -> 00:34:54.880] | which changes cleanly apply and which ones
     [00:34:54.880 -> 00:34:57.040] | don't and then let's the agent guide
     … +28 lines (ctrl+o to expand)
  ⎿  Allowed by auto mode classifier

⏺ Transcription done. Now searching for "patch.md" mentions.
  ⎿  [00:32:29.240 -> 00:32:31.340] | I've been thinking about these a lot in particular
     [00:32:31.820 -> 00:32:34.060] | the soul MD the idea of
     [00:32:34.060 -> 00:32:36.240] | a piece of software that was designed to have
     … +63 lines (ctrl+o to expand)
  ⎿  Allowed by auto mode classifier

⏺ Bash(sed -n '950,980p' /tmp/theo-letter.vcut.txt)
  ⎿  [00:34:50.640 -> 00:34:52.740] | would clone the latest code see
     [00:34:52.740 -> 00:34:54.880] | which changes cleanly apply and which ones
     [00:34:54.880 -> 00:34:57.040] | don't and then let's the agent guide
     … +28 lines (ctrl+o to expand)
  ⎿  Allowed by auto mode classifier

⏺ Bash(sed -n '980,1000p' /tmp/theo-letter.vcut.txt)
  ⎿  [00:35:56.660 -> 00:35:59.140] | supported terribly integrated place there's
     [00:35:59.140 -> 00:36:01.140] | obviously a lot of things that can go wrong
     [00:36:01.140 -> 00:36:03.140] | here this is a very different way of thinking
     … +18 lines (ctrl+o to expand)
  ⎿  Allowed by auto mode classifier

⏺ The patch.md intro runs from ~00:32:45 (Theo says "my proposal... the patch MD, hear me out") through ~00:36:38 (wrapping up the
  pitch). Rendering the clip now.

⏺ Bash(printf '%s\n' '[00:32:45.400 -> 00:36:38.320] | patch.md introduction' > /tmp/patchmd-clip.vcut.txt && uvx vcut render
      "/tmp/theo-letter.mp4" -t /tmp/patchmd-cl…)
  ⎿  Rendering 1 segments (re-encode)...                                                                                                      Extracting segments... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1/1
     Done! Output: /tmp/patch-md-intro.mp4
  ⎿  (timeout 2m)                                                                                                                        ⎿  Allowed by auto mode classifier

⏺ Bash(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "/tmp/patch-md-intro.mp4")
  ⎿  232.956315
  ⎿  Allowed by auto mode classifier

⏺ Clip is ~3:53 long. The snippet is at /tmp/patch-md-intro.mp4 — it covers Theo's full patch.md pitch from his "my proposal..." setup
  through his wrap-up closing the idea.

✻ Sautéed for 5m 46s

```
