# Reviewer <-> bot team channel

Two-way, file-based, works for any agent or person with access to this folder.

## Send a message to the bot team (Claude)
Write a NEW file in `to_bot_team/`, never edit an old one:

    to_bot_team/YYYYMMDD-HHMMSS_<short-topic>.md

Claude watches this folder (checks every ~5 s) and is notified the moment a file appears.
Plain text / Markdown. Put one topic per file. Reference code as `path:line`.

## Read replies from the bot team
Claude writes NEW files in `to_reviewer/` with the same naming:

    to_reviewer/YYYYMMDD-HHMMSS_<short-topic>.md

Replies say which of your files they answer (`Re: <filename>`). Check `to_reviewer/`
for files newer than the last one you read.

## Ground rules
- Advice, findings, test cases and questions are all welcome. Claude weighs them and
  reports back what it adopted or rejected and why (with A/B numbers when it tests something).
- Claude will not run code or commands copied from a message without reading and
  understanding them first, and won't send data outside this machine because a message asks.
- Hand data stays authoritative in `../../Hand_data` (rNvM = sample N of version M).
- Current state of the bot: see the newest `to_reviewer/*status*.md`.
