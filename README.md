# 🦁 shirOkhorshid CDN IP Scanner v1

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

**Scan thousands of IPs. Find CDN nodes. No limits.**

## What is shirOkhorshid?

A lightning-fast, pure Python IP scanner built for CDN detection. No ping dependencies. No subprocess headaches. Just raw speed.

- ⚡ 500+ concurrent connections (async I/O)
- 🎯 Detects Cloudflare, CloudFront, Akamai, Fastly
- 🖥️ Cross-platform: Windows, Linux, macOS
- ♾️ Zero artificial limits
- 🛑 Graceful Ctrl+C with auto-save

---

## Quick Start

### Windows (One-Click)
Double-click `scan.cmd` — it auto-installs, scans, saves, and opens results.

### Linux / macOS
```bash
pip install aiohttp
python scanner.py -i ip_list.txt
