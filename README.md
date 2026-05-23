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

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/0xnightraid/shirokhorshid-scanner.git
cd shirokhorshid-scanner

# Install requirements
### Step 1: Open CMD/Terminal in the scanner folder

### Step 2: Install requirements
pip install -r requirements.txt
```

## 📝 Prepare IP List

1.1.1.1                        # Single IP
8.8.8.8                        # Another single IP
192.168.1.0/24                 # CIDR range (254 IPs)
192.168.1.1-192.168.1.100      # Full range
10.0.0.1-254                   # Short range
104.16.124.96                  # Cloudflare IP
13.32.110.11                   # CloudFront IP

