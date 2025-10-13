cat top-1m.csv | cut -d',' -f2 | head -n 100000 | awk '{print   A}' > top-100k-queries.txt
