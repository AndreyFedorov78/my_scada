#!/usr/bin/env bash
# Живые показания на главной: WebSocket-листенер mosquitto (только чтение) + nginx /mqtt.
# Запуск с Мака из корня репозитория:   ssh andrey@tldev.ru 'bash -s' < deploy/setup_mqtt_ws.sh
# Повторный запуск безопасен (уже сделанные шаги пропускаются).
#
# Датчики не затрагиваются: 1883 остаётся анонимным и без ACL, mosquitto-ssl (8883) не трогаем.
# Перезапуск основного mosquitto отключит устройства на пару секунд — они переподключатся сами.
#
# Откат:  sudo cp <бэкап mosquitto.conf> /etc/mosquitto/mosquitto.conf
#         sudo rm /etc/systemd/system/mosquitto.service.d/override.conf && sudo systemctl daemon-reload
#         sudo systemctl restart mosquitto
#         sudo cp <бэкап nginx> /etc/nginx/sites-available/scada && sudo nginx -t && sudo systemctl reload nginx
set -euo pipefail
cd /home/andrey/www/my_scada
STAMP=$(date +%Y%m%d-%H%M%S)

devices() {  # какие датчики публикуют показания за 15 с
    timeout 15 mosquitto_sub -p 1883 -t 'my_scada/+/+' -v 2>/dev/null | cut -d' ' -f1 | cut -d/ -f2 | sort -u || true
}

echo "== датчики до перезапуска"
BEFORE=$(devices); echo "$BEFORE" | tr '\n' ' '; echo

echo "== mosquitto: WebSocket 9001 только чтение"
sudo cp /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.bak-$STAMP
echo "   бэкап /etc/mosquitto/mosquitto.conf.bak-$STAMP"
sudo cp deploy/ws.acl /etc/mosquitto/ws.acl
if ! grep -q per_listener_settings /etc/mosquitto/mosquitto.conf; then
    sudo python3 - <<'EOF'
p = "/etc/mosquitto/mosquitto.conf"
s = open(p).read()
anchor = "include_dir /etc/mosquitto/conf.d"
assert s.count(anchor) == 1, "не найден include_dir"
open(p, "w").write(s.replace(anchor, open("deploy/mosquitto-ws.conf").read() + "\n" + anchor))
EOF
fi

echo "== iptables: 9001 снаружи закрыт (правило ставится при каждом старте mosquitto)"
sudo mkdir -p /etc/systemd/system/mosquitto.service.d
sudo cp deploy/mosquitto-override.conf /etc/systemd/system/mosquitto.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart mosquitto
sleep 2
systemctl is-active mosquitto mosquitto-ssl
sudo ss -ltnp | grep -E ':1883|:8883|:9001'
sudo iptables -S INPUT | grep 9001
sudo ip6tables -S INPUT | grep 9001

echo "== nginx: /mqtt с проверкой входа"
sudo cp /etc/nginx/sites-available/scada /etc/nginx/sites-available/scada.bak-$STAMP
echo "   бэкап /etc/nginx/sites-available/scada.bak-$STAMP"
if ! grep -q 'location = /mqtt' /etc/nginx/sites-available/scada; then
    sudo python3 - <<'EOF'
p = "/etc/nginx/sites-available/scada"
s = open(p).read()
anchor = "    location / {"
assert s.count(anchor) == 2, "ожидалось два server с location /"   # scada.tldev.ru и i.tldev.ru
snippet = "".join(l for l in open("deploy/nginx-mqtt.conf") if not l.startswith("#"))
open(p, "w").write(s.replace(anchor, snippet + "\n" + anchor))
EOF
fi
sudo nginx -t
sudo systemctl reload nginx
echo -n "   /mqtt без входа (ждём 401): "; curl -s -o /dev/null -w '%{http_code}\n' https://scada.tldev.ru/mqtt
# что 9001 закрыт снаружи, проверять с другой машины:  nc -z -w3 tldev.ru 9001  (должно не соединиться)

echo "== датчики после перезапуска"
AFTER=$(devices); echo "$AFTER" | tr '\n' ' '; echo
MISSING=$(comm -23 <(echo "$BEFORE") <(echo "$AFTER"))
if [ -n "$MISSING" ]; then echo "!! не вернулись: $MISSING (подождите минуту и проверьте ещё раз)"; else echo "все датчики на месте"; fi
