# CLI Proxy API Key Manager

API Key management system for CLI Proxy API.

## Features

- Create API keys with expiration time
- Quick select time presets (1h, 6h, 12h, 1d, 7d, 30d, 90d, 1y, never expire)
- Edit and delete API keys
- Recycle bin for deleted keys
- Copy API keys with shareable templates
- Password protection
- Responsive design for PC and mobile

## Installation

```bash
pip install flask flask-cors pyyaml
python manager.py
```

## Configuration

Edit `config.yaml` to configure:
- Port number
- Password
- Auto-cleanup interval

## Usage

1. Access the web interface
2. Login with password (default: wlie0726)
3. Create new API keys with time presets
4. Copy keys with shareable templates
5. Edit or delete existing keys
6. Recover deleted keys from recycle bin
