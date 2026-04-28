# Changelog

## [1.8.0] - 2026-04-28
### Fixed
- Pin `mt5.initialize()` to the same MT5 terminal targeted by `find_mt5_window()` via process exe path. Resolves "Toggle attempt failed, state unchanged" when 2+ MT5 windows are open (state was being read from the wrong terminal).
- Log all matching MT5 window titles when multiple are found, so user can refine `mt5_keyword` to disambiguate.

## [1.7.0] - 2026-04-28
### Fixed
- Use `certifi` CA bundle for SSL on update check. Resolves `CERTIFICATE_VERIFY_FAILED` on VPS without system CA certs.

## [1.6.0] - 2026-04-27
### Added
- Auto-update check via GitHub Releases API; downloads new exe and swaps on exit.
### Fixed
- Foreground window flicker on toggle.

## [1.5.0] - 2026-04-26
### Fixed
- Improve algo toggle reliability; prevent VPS idle shutdown.

## [1.4.0] - 2026-04-25
### Fixed
- Rewrite `SendInput` with correct struct layout; add `WM_COMMAND` fallback for headless VPS toggling.

## [1.3.0] - 2026-04-24
### Added
- `.gitignore` and initial CHANGELOG scaffolding.

## [1.2.0] - 2026-03-30
### Fixed
- Resolve SetForegroundWindow error on long-running VPS sessions.

## [1.1.0] - 2025-xx-xx
### Added
- Initial upload with README.

## [1.0.0] - 2025-xx-xx
### Added
- Telegram bot control MT5 Algo Trading (on/off/status).
- System tray with Start/Stop/Edit Config/Exit.
- Config dialog (tkinter) on first run.
- Support multi-VPS, multi-bot in one Telegram group.
