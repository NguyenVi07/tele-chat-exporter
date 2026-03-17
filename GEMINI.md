# Tele-Chat-Exporter

A simple CLI tool to export Telegram chat history into various formats (TXT, JSON, CSV).

## Project Overview
- **Technology Stack:** Python 3.11+, Telethon, python-dotenv.
- **Package Manager:** `uv`.
- **Main Entry Point:** `main.py`.

## Core Features
- Export chat history to TXT, JSON, or CSV.
- Configurable sender name display (Name, ID, or Both).
- Optional inclusion of timestamps and sender IDs.
- Automatic directory creation under `export/` for each chat.

## Setup Requirements
1. **Telegram API Credentials:**
   - Obtain `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).
   - Create a `.env` file in the root directory:
     ```env
     API_ID=your_api_id
     API_HASH=your_api_hash
     ```
2. **Installation:**
   - Use `uv` to sync dependencies:
     ```bash
     uv sync
     ```

## Usage
Run the script using `uv`:
```bash
uv run main.py
```
The script will prompt you to:
1. Log in (on first run).
2. Select a chat from your dialog list.
3. Choose the export format and options.

## Development Notes
- The tool uses `Telethon`'s sync client.
- Sessions are stored in `my_session.session`.
- Exported files are saved in `export/<Chat_Name>/`.
- Message text is cleaned by replacing newlines with spaces for better readability in one-line formats.

## Roadmap / Ideas
- [ ] Support for media export (images, documents).
- [ ] Date range selection for exports.
- [ ] Improved error handling for rate limits.
- [ ] GUI version (maybe?).
