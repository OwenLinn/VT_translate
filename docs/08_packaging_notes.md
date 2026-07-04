# Packaging Notes

Packaging is not part of MVP.

Future packaging options:

- PyInstaller
- Nuitka

Before packaging:

- Make sure config can be created on first run
- Store user data in a safe local app data folder
- Do not bundle API keys
- Handle missing CUDA gracefully
- Provide CPU fallback or clear GPU installation guide
- Provide sample glossary
- Provide startup diagnostics

Future installer should include:

- app executable
- default config
- docs
- license
- model download instructions
