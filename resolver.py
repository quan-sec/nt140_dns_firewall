import socket
import cache
from dnslib import DNSRecord
import logging
from pathlib import Path

# Ensure logs/ directory next to this file and write logs there
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "dns.log"

# Cấu hình log -> write to logs/dns.log
logging.basicConfig(filename=str(LOG_FILE), level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

FORWARDER = ("8.8.8.8", 53)  # DNS upstream

def log_query(client_ip, domain, cache_hit=False):
    if cache_hit:
        logging.info(f"{client_ip} asked {domain} [CACHE]")
    else:
        logging.info(f"{client_ip} asked {domain} [FORWARD]")

def resolve(data, client_ip):
    query = DNSRecord.parse(data)
    qname = str(query.q.qname)
    qtype = query.q.qtype
    key = (qname, qtype)

    # Kiểm tra cache
    cached = cache.get(key)
    if cached:
        log_query(client_ip, qname, cache_hit=True)
        return cached

    # Forward query đến DNS upstream
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    sock.sendto(data, FORWARDER)
    response_data, _ = sock.recvfrom(512)

    # Lưu cache với TTL từ bản ghi trả về (lấy TTL bản ghi đầu tiên)
    response = DNSRecord.parse(response_data)
    ttl = response.rr[0].ttl if response.rr else 60
    cache.put(key, response_data, ttl)

    log_query(client_ip, qname, cache_hit=False)
    return response_data
