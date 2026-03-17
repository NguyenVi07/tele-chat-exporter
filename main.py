import sys
import json
import csv
import os
from telethon.sync import TelegramClient
from telethon.utils import get_display_name
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Starting Tele-Chat-Exporter...")

# Get credentials from .env
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')

if not api_id or not api_hash:
    print("\n[ERROR] API_ID or API_HASH not found in .env file.")
    print("Please create a .env file with your credentials.")
    sys.exit()

try:
    api_id = int(api_id)
except ValueError:
    print("\n[ERROR] API_ID must be a number.")
    sys.exit()

print("Connecting to Telegram...")
client = TelegramClient('my_session', api_id, api_hash)
client.start()

print("\n--- Fetching your Chat list... ---")
dialogs = client.get_dialogs()

for i, d in enumerate(dialogs):
    print(f"{i}: {d.name} (ID: {d.id})")

index_str = input("\nEnter the number of the chat you want to export: ")
try:
    index = int(index_str)
    target_group = dialogs[index]
except (ValueError, IndexError):
    print("Invalid number. Please run the tool again.")
    sys.exit()

# 1. Select Format
print("\nSelect export format:")
print("1. TXT")
print("2. JSON")
print("3. CSV")
fmt_choice = input("Enter number (1, 2, or 3): ").strip()

# 2. Select Name Display
print("\nSelect sender name format:")
print("1. Name only (e.g., John Doe)")
print("2. ID only (e.g., 123456789)")
print("3. Both (e.g., John Doe [123456789])")
name_choice = input("Enter number (1, 2, or 3): ").strip()

# 3. Advanced Options based on Format
inc_time_txt = False
inc_time_jc = False
inc_id_jc = False

if fmt_choice == '1':
    # Ask for TXT
    ans_time = input("\nInclude timestamp in TXT? (y/n): ").strip().lower()
    if ans_time == 'y':
        inc_time_txt = True
else:
    # Ask for JSON/CSV
    ans_time = input("\nInclude 'time' field? (y/n): ").strip().lower()
    if ans_time == 'y':
        inc_time_jc = True
        
    ans_id = input("Include separate 'sender_id' field? (y/n): ").strip().lower()
    if ans_id == 'y':
        inc_id_jc = True

print(f"\nStarting export for: {target_group.name}...")

messages_data = []
count = 0

# Fetch messages
for message in client.iter_messages(target_group):
    if not message.text:
        continue
    
    sender = message.sender
    name = get_display_name(sender) if sender else "Unknown"
    sender_id = str(message.sender_id) if message.sender_id else "N/A"

    # Handle display name
    if name_choice == '1':
        display_name = name
    elif name_choice == '2':
        display_name = sender_id
    else:
        display_name = f"{name} [{sender_id}]"

    timestamp = str(message.date)
    # Replace newlines with spaces for cleaner one-line reading
    clean_text = message.text.replace('\n', ' ')

    # Build data dictionary
    if fmt_choice == '1':
        # TXT structure
        data_dict = {
            "sender": display_name,
            "message": clean_text,
            "time": timestamp
        }
    else:
        # JSON/CSV structure
        data_dict = {"sender": display_name, "message": clean_text}
        if inc_id_jc:
            data_dict["sender_id"] = sender_id
        if inc_time_jc:
            data_dict["time"] = timestamp

    messages_data.append(data_dict)

    count += 1
    if count % 100 == 0:
        print(f"Fetched {count} messages...")

if not messages_data:
    print("No text messages found in this chat.")
    sys.exit()

# Reverse to chronological order (oldest first)
messages_data.reverse()

# --- FOLDER CREATION LOGIC ---

# 1. Create safe name for Folder and File
# Allow alphanumeric, spaces, underscores, and hyphens
safe_name = "".join([c for c in target_group.name if c.isalnum() or c in (' ', '_', '-')]).strip()

# Fallback if name becomes empty (e.g. only emojis)
if not safe_name:
    safe_name = f"chat_{target_group.id}"

# 2. Define Paths
base_export_dir = "export"
# Structure: export/ChatName/
chat_export_dir = os.path.join(base_export_dir, safe_name)

# 3. Create Directories (if they don't exist)
os.makedirs(chat_export_dir, exist_ok=True)

# 4. Define full file path
if fmt_choice == '1':
    filename = f"{safe_name}.txt"
    file_path = os.path.join(chat_export_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        for m in messages_data:
            if inc_time_txt:
                f.write(f"[{m['time']}] {m['sender']}: {m['message']}\n")
            else:
                f.write(f"{m['sender']}: {m['message']}\n")

elif fmt_choice == '2':
    filename = f"{safe_name}.json"
    file_path = os.path.join(chat_export_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(messages_data, f, ensure_ascii=False, indent=4)

elif fmt_choice == '3':
    filename = f"{safe_name}.csv"
    file_path = os.path.join(chat_export_dir, filename)
    
    keys = messages_data[0].keys()
    with open(file_path, "w", encoding="utf-8-sig", newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(messages_data)

print(f"\n--- SUCCESS! ---")
print(f"Directory created: {os.path.abspath(chat_export_dir)}")
print(f"File saved to: {os.path.abspath(file_path)}")