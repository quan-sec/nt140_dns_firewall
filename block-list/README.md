# Hướng dẫn sử dụng Block-list

Tài liệu này hướng dẫn cách sử dụng hệ thống blocklist để chặn các domain độc hại trong DNS firewall.

## Tổng quan

Block-list là một thành phần quan trọng của DNS firewall, cho phép chặn truy vấn DNS tới các domain độc hại, quảng cáo hoặc không mong muốn. Hệ thống bao gồm:

- Script thu thập và cập nhật danh sách chặn từ các nguồn threat feeds
- Module kiểm tra domain có trong danh sách chặn hay không
- File blacklist chứa danh sách domain cần chặn

## Cấu trúc thư mục

```
block-list/
├── README.md          # Tài liệu này
├── API_Update.py      # Script cập nhật blacklist từ các nguồn
├── blocklist.py       # Module kiểm tra domain
└── blacklist.txt      # File chứa danh sách domain cần chặn
```

## Yêu cầu hệ thống

- **Python**: >= 3.7
- **Thư viện cần thiết**:
  - `requests` - để tải dữ liệu từ các API
  - `tldextract` - để xử lý domain
  - `watchdog` - để theo dõi thay đổi file

### Cài đặt thư viện

```cmd
pip install requests tldextract watchdog
```

## Cách sử dụng

### 1. Tạo/Cập nhật blacklist

#### Tạo blacklist một lần:

```cmd
python API_Update.py --once
```

#### Chạy cập nhật định kỳ (daemon):

```cmd
python API_Update.py --daemon --interval 3600
```

**Tham số**:

- `--interval`: thời gian giữa các lần cập nhật (giây)
- `--candidate`: ghi ra file tạm `blacklist.candidate.txt` thay vì ghi đè file chính

#### Import trong code Python:

```python
from API_Update import start_periodic

# Khởi động cập nhật định kỳ mỗi 1 giờ
start_periodic(interval_seconds=3600)
```

### 2. Sử dụng blocklist để kiểm tra domain

#### Đọc và kiểm tra domain:

```python
from blocklist import load_blacklist, is_blocked

# Nạp danh sách chặn
exact, wildcard, regex = load_blacklist()

# Kiểm tra domain
domain = "malicious.com"
if is_blocked(domain, exact, wildcard, regex):
    print(f"Domain {domain} bị chặn!")
else:
    print(f"Domain {domain} được phép.")
```

#### Tự động reload khi blacklist thay đổi:

```python
from blocklist import watch_blacklist

def reload_callback():
    print("Blacklist đã được cập nhật!")
    # Reload lại danh sách
    global exact, wildcard, regex
    exact, wildcard, regex = load_blacklist()

# Theo dõi thay đổi file
observer = watch_blacklist("blacklist.txt", reload_callback)
```

### 3. Định dạng file blacklist.txt

File `blacklist.txt` có định dạng đơn giản:

- Mỗi dòng chứa một domain
- Dòng bắt đầu bằng `#` là comment
- Dòng trống được bỏ qua

**Ví dụ**:

```
# Danh sách domain độc hại
malware.example.com
phishing.badsite.net
ads.tracker.org

# Domain quảng cáo
*.googleads.com
*.doubleclick.net
```

**Các định dạng hỗ trợ**:

- **Exact match**: `badsite.com` - chặn chính xác domain này
- **Wildcard**: `*.ads.com` - chặn tất cả subdomain của ads.com
- **Regex**: `^.*\\.malware\\.(com|net)$` - chặn theo pattern regex

## Tích hợp vào DNS resolver

Để tích hợp blocklist vào DNS resolver, thêm kiểm tra trong `resolver.py`:

```python
import blocklist

# Nạp blacklist khi khởi động
exact, wildcard, regex = blocklist.load_blacklist("block-list/blacklist.txt")

def resolve(data, client_ip):
    query = DNSRecord.parse(data)
    qname = str(query.q.qname).rstrip('.')

    # Kiểm tra blacklist
    if blocklist.is_blocked(qname, exact, wildcard, regex):
        # Trả về NXDOMAIN hoặc IP giả
        return create_blocked_response(query)

    # Tiếp tục xử lý bình thường
    # ... rest of resolve logic
```

## Quản lý và bảo trì

### Backup blacklist

```cmd
copy block-list\blacklist.txt block-list\blacklist.backup.txt
```

### Làm sạch blacklist (loại bỏ comment và dòng trống)

```cmd
findstr /V "^#" block-list\blacklist.txt | findstr /V "^$" > block-list\blacklist.clean.txt
```

### Kiểm tra số lượng domain trong blacklist

```cmd
findstr /V "^#" block-list\blacklist.txt | findstr /V "^$" | find /C /V ""
```

### Thêm domain mới vào blacklist

```cmd
echo new-malicious-domain.com >> block-list\blacklist.txt
```

## Nguồn threat feeds

Script `API_Update.py` thu thập dữ liệu từ các nguồn như:

- **OpenPhish**: Danh sách domain phishing
- **StevenBlack**: Tổng hợp nhiều nguồn ads/malware
- **URLhaus**: Database malware URLs
- **Custom feeds**: Có thể thêm nguồn riêng

Để thêm nguồn mới, chỉnh sửa biến `SOURCES` trong `API_Update.py`.

## Lưu ý quan trọng

1. **Performance**: Với blacklist lớn (>100k domain), nên optimize thuật toán lookup
2. **Memory**: Blacklist được nạp vào RAM, cần tính toán memory usage
3. **Update frequency**: Cân nhắc tần suất cập nhật vs tải hệ thống
4. **False positives**: Thường xuyên kiểm tra và loại bỏ domain bị chặn nhầm
5. **Logging**: Ghi log các domain bị chặn để phân tích và debug

## Troubleshooting

### Lỗi thường gặp:

**1. Không tải được threat feeds**

```
Kiểm tra kết nối internet và proxy settings
Xem log lỗi trong API_Update.py
```

**2. Blacklist không được reload**

```
Kiểm tra watchdog service đang chạy
Verify file permissions cho blacklist.txt
```

**3. Domain không bị chặn như mong đợi**

```
Kiểm tra format domain trong blacklist.txt
Test regex pattern nếu sử dụng
```

## Đóng góp

- **Thêm domain**: Tạo pull request hoặc issue với domain cần chặn
- **Báo false positive**: Báo cáo domain bị chặn nhầm
- **Cải tiến code**: Đóng góp tối ưu performance hoặc tính năng mới

---

_Tài liệu được cập nhật: October 2025_
