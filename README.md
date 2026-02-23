# kindle-weather

Scripts and assets for generating a Kindle weather display image.

## Security hardening updates

- Weather data is fetched over **HTTPS** instead of HTTP.
- The Python script now uses Python 3 and applies a network timeout for outbound requests.
- XML parsing uses secure Expat protections to reduce XML entity risks.
- Remote icon identifiers are validated against a strict allowlist before being inserted into SVG.
- The shell runner now fails fast (`set -eu`) and uses `install` with explicit file mode when copying output.
