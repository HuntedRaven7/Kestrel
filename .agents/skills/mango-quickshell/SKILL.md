---
name: mango-quickshell
description: Mango compositor, Quickshell, rofi, ghostty, awww integration
---
# Mango + Quickshell

Mango 0.17.2 needs wlroots-0.20 (≥0.20.0) + scenefx-0.5 (≥0.5.0) —
packaged versioned as wlroots0.20; neither is in the Hummingbird overlay.
Mango also needs libcjson + pangocairo (Fedora buildroot only for now). Quickshell v0.3.1 needs Qt ≥6.6 + private headers;
rebuild on every Qt bump. No default `shell.qml` shipped (user-owned).
Mango config = upstream default; rofi + ghostty from Pigeon; awww as user unit.
