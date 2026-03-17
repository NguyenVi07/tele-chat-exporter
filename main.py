import sys
import json
import csv
import os
import asyncio
import re
import shutil
from telethon import TelegramClient
from telethon.utils import get_display_name
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

# Load environment variables
load_dotenv()

# Regex patterns
MULTIPART_PATTERN = re.compile(r"^(.*?)\.\d{3}$")
ARCHIVE_PATTERN = re.compile(r"\.(zip|rar|7z|tar|gz|bz2|00\d)$", re.IGNORECASE)

# Global set to track finished downloads for cleanup
finished_paths = set()

def get_file_info(message):
    filename = ""
    file_size = 0
    if message.media:
        if hasattr(message.media, 'document'):
            file_size = message.media.document.size
            for attr in message.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    filename = attr.file_name
                    break
            if not filename: filename = f"doc_{message.id}"
        elif hasattr(message.media, 'photo'):
            file_size = message.media.photo.sizes[-1].size
            filename = f"photo_{message.id}.jpg"
    return filename, file_size

async def download_task(client, message, target_path, semaphore, pbar):
    async with semaphore:
        try:
            path = await client.download_media(message, target_path)
            if path:
                finished_paths.add(os.path.abspath(target_path))
                _, size = get_file_info(message)
                pbar.update(size)
                return os.path.basename(path)
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
        return None

async def main():
    media_to_download = [] 
    chat_export_dir = ""
    
    try:
        print("Starting Tele-Chat-Exporter...")

        api_id = os.getenv('API_ID')
        api_hash = os.getenv('API_HASH')

        if not api_id or not api_hash:
            print("\n[ERROR] API_ID or API_HASH not found in .env file.")
            return

        try:
            api_id = int(api_id)
        except ValueError:
            print("\n[ERROR] API_ID must be a number.")
            return

        print("Connecting to Telegram...")
        client = TelegramClient('my_session', api_id, api_hash)
        await client.start()

        print("\n--- Fetching your Chat list... ---")
        dialogs = await client.get_dialogs()

        for i, d in enumerate(dialogs):
            print(f"{i}: {d.name} (ID: {d.id})")

        index_str = input("\nEnter the number of the chat you want to export: ")
        try:
            index = int(index_str)
            target_group = dialogs[index]
        except (ValueError, IndexError):
            print("Invalid number.")
            return

        # --- OPTIONS ---
        ans_export_text = input("\nDo you want to export text messages? (y/n): ").strip().lower()
        export_text = (ans_export_text == 'y')

        fmt_choice, name_choice = '1', '1'
        inc_time_txt, inc_time_jc, inc_id_jc = False, False, False

        if export_text:
            print("\nSelect export format: 1. TXT | 2. JSON | 3. CSV")
            fmt_choice = input("Enter (1-3): ").strip()
            print("\nSelect sender name format: 1. Name | 2. ID | 3. Both")
            name_choice = input("Enter (1-3): ").strip()
            if fmt_choice == '1':
                inc_time_txt = input("\nInclude timestamp in TXT? (y/n): ").strip().lower() == 'y'
            else:
                inc_time_jc = input("\nInclude 'time' field? (y/n): ").strip().lower() == 'y'
                inc_id_jc = input("Include separate 'sender_id' field? (y/n): ").strip().lower() == 'y'

        ans_media = input("\nDownload media (images, docs, etc.)? (y/n): ").strip().lower()
        download_media = (ans_media == 'y')
        
        archive_only = False
        if download_media:
            print("\nMedia download options: 1. ALL | 2. Archives ONLY (.zip, .rar, .001...)")
            archive_only = (input("Enter (1 or 2): ").strip() == '2')

        # --- PATH SETUP ---
        safe_name = "".join([c for c in target_group.name if c.isalnum() or c in (' ', '_', '-')]).strip()
        if not safe_name: safe_name = f"chat_{target_group.id}"
        
        chat_export_dir = os.path.join("export", safe_name)
        media_dir = os.path.join(chat_export_dir, "media")
        os.makedirs(chat_export_dir, exist_ok=True)

        # --- SCANNING PHASE ---
        if not export_text:
            print(f"\nCalculating media size for: {target_group.name}... Please wait.")
        else:
            print(f"\nScanning messages (Processing text & calculating media size)...")
        
        messages_data = []
        total_size = 0
        count = 0

        async for message in client.iter_messages(target_group):
            fname, fsize = get_file_info(message)
            is_archive = (fname and ARCHIVE_PATTERN.search(fname))

            if download_media:
                is_target = (archive_only and is_archive) or (not archive_only and message.media)
                if is_target:
                    target_subdir = media_dir
                    match = MULTIPART_PATTERN.match(fname)
                    if match:
                        target_subdir = os.path.join(media_dir, match.group(1))
                    
                    target_path = os.path.join(target_subdir, fname)
                    media_to_download.append((message, target_path, fsize))
                    total_size += fsize
                    
                    # "La làng" if text export is disabled
                    if not export_text:
                        print(f"[SCAN] Found: {fname} | Total: {total_size/(1024*1024):.2f} MB")

            if export_text:
                if not message.text and not message.media: continue
                sender = await message.get_sender()
                name = get_display_name(sender) if sender else "Unknown"
                sender_id = str(message.sender_id) if message.sender_id else "N/A"
                dname = name if name_choice=='1' else sender_id if name_choice=='2' else f"{name} [{sender_id}]"
                clean_text = message.text.replace('\n', ' ') if message.text else ""
                
                if fmt_choice == '1':
                    data_dict = {"sender": dname, "message": clean_text, "time": str(message.date), "media": fname if message.media else None}
                else:
                    data_dict = {"sender": dname, "message": clean_text, "media": fname if message.media else None}
                    if inc_id_jc: data_dict["sender_id"] = sender_id
                    if inc_time_jc: data_dict["time"] = str(message.date)
                messages_data.append(data_dict)

            count += 1
            if count % 200 == 0 and export_text:
                print(f"Scanned {count} messages...")

        # --- AUTOMATIC DISK RESERVATION ---
        if download_media and media_to_download:
            usage = shutil.disk_usage(chat_export_dir)
            total_mb = total_size / (1024*1024)
            free_mb = usage.free / (1024*1024)
            
            print(f"\nDisk Report: Required {total_mb:.2f} MB | Available {free_mb:.2f} MB")
            
            if usage.free < total_size:
                print(f"[FATAL] Not enough disk space! Need {total_mb - free_mb:.2f} MB more.")
                return
            
            print("Automatically reserving disk space (Pre-allocation)...")
            for _, path, size in media_to_download:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    if size > 0: f.truncate(size)
            print("Space reserved successfully.")

        # --- STEP 1: EXPORT TEXT ---
        if export_text and messages_data:
            messages_data.reverse()
            ext = ".txt" if fmt_choice=='1' else ".json" if fmt_choice=='2' else ".csv"
            file_path = os.path.join(chat_export_dir, safe_name + ext)
            with open(file_path, "w", encoding="utf-8" if fmt_choice!='3' else "utf-8-sig", newline='' if fmt_choice=='3' else None) as f:
                if fmt_choice == '1':
                    for m in messages_data:
                        line = f"[{m['time']}] " if inc_time_txt else ""
                        line += f"{m['sender']}: {m['message']}" + (f" [Media: {m['media']}]" if m['media'] else "") + "\n"
                        f.write(line)
                elif fmt_choice == '2':
                    json.dump(messages_data, f, ensure_ascii=False, indent=4)
                elif fmt_choice == '3':
                    writer = csv.DictWriter(f, fieldnames=messages_data[0].keys())
                    writer.writeheader()
                    writer.writerows(messages_data)
            print(f"\nTEXT EXPORT SUCCESS: {os.path.basename(file_path)}")

        # --- STEP 2: DOWNLOAD MEDIA ---
        if download_media and media_to_download:
            print(f"\nStarting high-speed download: {len(media_to_download)} files...")
            semaphore = asyncio.Semaphore(10)
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading", colour='green') as pbar:
                tasks = [asyncio.create_task(download_task(client, m, p, semaphore, pbar)) for m, p, s in media_to_download]
                try:
                    await asyncio.gather(*tasks)
                except asyncio.CancelledError:
                    for t in tasks: t.cancel()
                    raise

        print(f"\n--- ALL DONE! ---")
        print(f"Project saved in: {os.path.abspath(chat_export_dir)}")

    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Operation aborted by user.")
        print("Cleaning up unfinished files (releasing reserved space)...")
        try:
            for _, path, _ in media_to_download:
                abs_p = os.path.abspath(path)
                if abs_p not in finished_paths and os.path.exists(abs_p):
                    os.remove(abs_p)
            print("Cleanup complete.")
        except NameError:
            pass 
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
