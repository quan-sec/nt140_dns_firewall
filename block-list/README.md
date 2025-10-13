# Hướng dẫn sử dụng và cài đặt: API_Update.py & blocklist.py

## 1. Giới thiệu

- **API_Update.py**: Tự động tải, tổng hợp các nguồn threat feeds (OpenPhish, StevenBlack, URLhaus...) và tạo file `blacklist.txt` chứa danh sách domain độc hại.
- **blocklist.py**: Đọc file `blacklist.txt`, kiểm tra domain có bị chặn không, hỗ trợ tự động reload khi file blacklist thay đổi.

## 2. Yêu cầu cài đặt

- Python >= 3.7
- Các thư viện:
  - requests
  - tldextract
  - watchdog

### Cài đặt thư viện

Chạy lệnh sau trong thư mục dự án:

```cmd
pip install requests tldextract watchdog
```

## 3. Sử dụng API_Update.py

### Tạo blacklist.txt một lần

```cmd
python API_Update.py --once
```

### Chạy cập nhật định kỳ (daemon)

```cmd
python API_Update.py --daemon --interval 3600
```

- `--interval`: thời gian giữa các lần cập nhật (giây)
- `--candidate`: ghi ra file tạm `blacklist.candidate.txt` thay vì ghi đè file chính

### Import và chạy trong chương trình khác

```python
from API_Update import start_periodic
start_periodic(interval_seconds=3600)
```

## 4. Sử dụng blocklist.py

### Đọc blacklist

```python
from blocklist import load_blacklist, is_blocked
exact, wildcard, regex = load_blacklist()
print(is_blocked("malicious.com", exact, wildcard, regex))
```

### Tự động reload khi blacklist thay đổi

```python
def reload_callback():
    print("Blacklist vừa được cập nhật!")
    # reload lại danh sách
    global exact, wildcard, regex
    exact, wildcard, regex = load_blacklist()

from blocklist import watch_blacklist
observer = watch_blacklist("blacklist.txt", reload_callback)
```

## 5. Lưu ý

- File `blacklist.txt` sẽ được ghi đè mỗi lần cập nhật.
- Nên kiểm tra và backup file blacklist nếu cần.
- Có thể chỉnh sửa nguồn threat feeds trong biến `SOURCES` của API_Update.py.

---


