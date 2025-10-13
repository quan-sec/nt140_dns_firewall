# DNS Firewall

# Clone repo
    git clone https://github.com/quan-sec/nt140_dns_firewall
# Copy vào /opt/dns_firewall hoặc vị trí khác 
    sudo cp nt140_dns_firewall/* -r /opt/dns_firewall

# Tạo dịch vụ systemd dns_firewall:
    sudo nano /etc/systemd/system/dns-firewall.service
####
[Unit]
Description=Python DNS Firewall
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/dns_firewall
ExecStart=/opt/dns_firewall/venv/bin/python3 /opt/dns_firewall/server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
####

# Cấu hình systemd-resolved 
    sudo nano /etc/systemd/resolved.conf
####
Tìm và chỉnh sửa các dòng trong mục [Resolve]

[Resolve]
DNS=127.0.0.1
FallbackDNS=1.1.1.1 8.8.8.8
DNSStubListener=yes
####

# Áp dụng 
    sudo systemctl daemon-reload
    sudo systemctl restart systemd-resolved
    sudo systemctl enable --now dns-firewall.service