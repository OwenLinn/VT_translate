# Requirements

## Confirmed User Requirements

- Windows desktop application
- Capture YouTube livestream audio from system output
- Support English and Japanese livestreams
- Translate into Traditional Chinese or Simplified Chinese
- Display subtitles in a floating draggable window
- Subtitle window must be always-on-top
- Font size, font color, background color, and transparency must be configurable
- User can manually create glossary entries
- Glossary should prevent incorrect translation of names, game terms, characters,
  abilities, items, places, etc.
- AI-assisted high-frequency term extraction is planned for later stages
- Development should be staged and test-driven
- Project should include documentation and development logs
- User can choose the DeepSeek translation model: `deepseek-v4-flash` or
  `deepseek-v4-pro`

## MVP Requirements

Stage 1 to Stage 4 should complete:

1. Project scaffold
2. Configuration loading
3. DeepSeek translation smoke test
4. Audio capture smoke test
5. ASR file smoke test
6. Terminal real-time pipeline
7. Basic overlay subtitle window
8. Manual glossary support

## Non-MVP Features

Do not implement these initially:

- Chrome extension
- Automatic YouTube subtitle extraction
- Full local translation model
- Cloud account system
- Shared glossary platform
- Dubbing / voice replacement
- Multi-speaker diarization
