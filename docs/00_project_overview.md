# Project Overview

This project is a Windows desktop application for real-time translation
subtitles during YouTube livestream viewing.

The application captures system audio, performs local ASR for English/Japanese
speech, translates the recognized text into Traditional or Simplified Chinese,
and displays subtitles in a draggable always-on-top overlay window.

## Main Goals

- Real-time subtitle translation
- Local ASR with GPU acceleration
- Translation quality suitable for livestream watching
- Glossary support for names and game terms
- Customizable subtitle overlay
- Local-first storage
- Future packaging support

## Target Platform

- Windows 10/11
- NVIDIA GPU preferred
- Python 3.11 recommended

## Core Pipeline

```text
Audio capture
-> VAD
-> ASR
-> Translation
-> Glossary correction
-> Subtitle overlay
```
