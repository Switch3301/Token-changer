# Token-Changer
A tool that generates a new Discord token by exploiting the QR code login system.

## What This Actually Does
This script:
1. Takes your existing Discord token
2. Connects to Discord's remote authentication system
3. Creates a new token by simulating a QR code scan
4. Invalidates your old token by logging it out
5. Gives you the new token

No password is needed because Discord's QR code login system doesn't require one. When you scan a QR code with your phone in Discord, you're authenticating without re-entering your password - this script does exactly that but programmatically.

## Installation
```bash
pip install websocket-client curl_cffi cryptography
```

## Usage
```python
# Run the script
python main.py

# Or import and use in your code
from main import run
new_token = run("your_old_token")  # Old token will be invalidated
```

## Platform Support
- Linux: Uses Chrome 131 impersonation by default
- Windows: Change `impersonate="chrome131"` to `impersonate="chrome124"`

## Proxies
Recommended: [Outpost Proxies](https://outpostproxies.com/)

Using proxies is essential to avoid Discord's rate limits and IP bans. Outpost offers:
- Ultra-fast US proxies (under 200ms response time)
- Unlimited bandwidth with no transfer restrictions
- Private, dedicated IPs for maximum security
- Enterprise-grade stability with 99.9% uptime

## Warning
**IMPORTANT**: This tool is for educational purposes only. Using this tool:
- Violates Discord's Terms of Service
- May result in account termination
- Could lead to IP bans or other restrictions
- Should not be used for unauthorized access to accounts

By using this tool, you accept full responsibility for any consequences. The developers are not responsible for any misuse or resulting account actions.

## Contact
Discord: 2b292e2760362f2e / https://discord.gg/switchuwu
