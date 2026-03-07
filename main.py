import sys
import json
import csv
import os
from telethon.sync import TelegramClient
from telethon.utils import get_display_name

print("Đang khởi động tool nha Vỹ...")

api_id = 31406154
api_hash = '3bf8fd8df537918ef78ce3a3d0705fb2'

print("Đang kết nối vào Telegram...")
client = TelegramClient('my_session', api_id, api_hash)
client.start()

print("\n--- Đang tải danh sách Chat của ông... ---")
dialogs = client.get_dialogs()

for i, d in enumerate(dialogs):
    print(f"{i}: {d.name} (ID: {d.id})")

index_str = input("\nNhập số thứ tự của Group muốn lấy: ")
try:
    index = int(index_str)
    target_group = dialogs[index]
except (ValueError, IndexError):
    print("Số ông nhập không đúng rồi, chạy lại nhé!")
    sys.exit()

# 1. Chọn định dạng xuất
print("\nChọn định dạng xuất:")
print("1. TXT (Dễ đọc nhất cho NVDA)")
print("2. JSON (Dữ liệu cho lập trình)")
print("3. CSV (Mở bằng Excel)")
fmt_choice = input("Nhập số (1, 2 hoặc 3): ").strip()

# 2. Chọn cách hiển thị Tên (Dùng chung)
print("\nChọn cách hiển thị tên người gửi:")
print("1. Chỉ Tên")
print("2. Chỉ ID")
print("3. Cả hai (Tên [ID])")
name_choice = input("Nhập số (1, 2 hoặc 3): ").strip()

# 3. Các tùy chọn nâng cao theo định dạng (Dùng Y/N)
inc_time_txt = False
inc_time_jc = False
inc_id_jc = False

if fmt_choice == '1':
    # Hỏi cho TXT
    ans_time = input("\nÔng có muốn kèm theo Thời gian không? (y/n): ").strip().lower()
    if ans_time == 'y':
        inc_time_txt = True
else:
    # Hỏi cho JSON và CSV
    ans_time = input("\nCó giữ trường Thời gian (Date/Time) không? (y/n): ").strip().lower()
    if ans_time == 'y':
        inc_time_jc = True
        
    ans_id = input("Có giữ trường ID người gửi (Sender ID) riêng không? (y/n): ").strip().lower()
    if ans_id == 'y':
        inc_id_jc = True

print(f"\nĐang bắt đầu lấy tin nhắn từ: {target_group.name}...")

messages_data = []
count = 0

for message in client.iter_messages(target_group):
    if not message.text:
        continue
    
    sender = message.sender
    name = get_display_name(sender) if sender else "Unknown"
    sender_id = str(message.sender_id) if message.sender_id else "N/A"

    # Xử lý tên hiển thị
    if name_choice == '1':
        display_name = name
    elif name_choice == '2':
        display_name = sender_id
    else:
        display_name = f"{name} [{sender_id}]"

    timestamp = str(message.date)
    clean_text = message.text.replace('\n', ' ')

    # Xây dựng dữ liệu tùy theo định dạng
    if fmt_choice == '1':
        # Dữ liệu cho TXT
        data_dict = {
            "sender": display_name,
            "message": clean_text,
            "time": timestamp
        }
    else:
        # Dữ liệu cho JSON / CSV (động theo Y/N)
        data_dict = {"sender": display_name, "message": clean_text}
        if inc_id_jc:
            data_dict["sender_id"] = sender_id
        if inc_time_jc:
            data_dict["time"] = timestamp

    messages_data.append(data_dict)

    count += 1
    if count % 100 == 0:
        print(f"Đã lấy được {count} tin nhắn...")

if not messages_data:
    print("Không tìm thấy tin nhắn nào cả!")
    sys.exit()

# Đảo ngược để tin cũ ở trên, mới ở dưới
messages_data.reverse()

# Tạo tên file an toàn
safe_name = "".join([c for c in target_group.name if c.isalnum() or c in (' ', '_')]).strip()

# 4. Lưu file dựa trên lựa chọn
if fmt_choice == '1':
    file_path = f"{safe_name}.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        for m in messages_data:
            if inc_time_txt:
                f.write(f"{m['sender']}: {m['message']} : {m['time']}\n")
            else:
                f.write(f"{m['sender']}: {m['message']}\n")

elif fmt_choice == '2':
    file_path = f"{safe_name}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(messages_data, f, ensure_ascii=False, indent=4)

elif fmt_choice == '3':
    file_path = f"{safe_name}.csv"
    keys = messages_data[0].keys()
    with open(file_path, "w", encoding="utf-8-sig", newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(messages_data)

print(f"\n--- XONG RỒI VỸ ƠI! ---")
print(f"File lưu tại: {os.path.abspath(file_path)}")