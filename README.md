# Tele-Chat-Exporter

A simple, fast, and fully accessible CLI tool to export Telegram chat history to TXT, JSON, or CSV.

## 🚀 Getting Started

### 1. Install `uv` (Recommended)
This project uses `uv` for extremely fast Python package management. If you are on Windows, you can install it easily using **winget**:

```powershell
winget install -e --id astral-sh.uv
```

*Note: After installation, you might need to restart your terminal (PowerShell/CMD) for the `uv` command to be recognized.*

### 2. Configure Environment Variables
To connect to Telegram, you need to provide your API credentials.

1.  Go to [my.telegram.org](https://my.telegram.org) and log in with your phone number.
2.  Click on **API development tools**.
3.  Create a new application (you can use any name).
4.  Copy your `App api_id` and `App api_hash`.
5.  In the project root directory, create a new file named `.env` and paste your credentials like this:

```env
API_ID=your_api_id_here
API_HASH=your_api_hash_here
```

### 3. Installation & Usage
Once `uv` is installed and your `.env` is ready, just run:

```powershell
# Sync dependencies and run the app
uv run main.py
```

`uv` will automatically create a virtual environment, install the required libraries (`Telethon`, `python-dotenv`), and start the script.

## 📂 Export Options
The tool will prompt you to:
1. Log in (on first run).
2. Select a chat from your dialog list.
3. Choose the export format and options (timestamps, sender IDs, etc.).

Exported files are saved in the `export/<Chat_Name>/` directory.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
