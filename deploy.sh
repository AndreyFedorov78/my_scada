#!/usr/bin/env bash
# Автодеплой ветки production на сервере tldev.ru. Запускается по cron (с flock от наложения).
# Делает что-то только если в origin/production появился новый коммит.
# Расписание: */2 * * * * (crontab пользователя andrey), лог в deploy.log.
set -euo pipefail

cd /home/andrey/www/my_scada
BRANCH=production
PY=/home/andrey/www/my_scada/env/bin/python
PIP=/home/andrey/www/my_scada/env/bin/pip

git fetch -q origin "$BRANCH"
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")
[ "$LOCAL" = "$REMOTE" ] && exit 0   # нечего деплоить

echo "=== $(date '+%F %T') deploy ${LOCAL:0:7} -> ${REMOTE:0:7} ==="

# Ставим зависимости только если изменился requirements.txt
REQ_CHANGED=$(git diff --name-only "$LOCAL" "$REMOTE" -- requirements.txt)

git pull --ff-only origin "$BRANCH"

if [ -n "$REQ_CHANGED" ]; then
    echo "requirements.txt изменён — pip install"
    $PIP install -q -r requirements.txt
fi

$PY manage.py migrate --noinput
# Статику отдаёт nginx прямо из static/ репозитория — collectstatic не нужен.
sudo -n systemctl restart gunicorn_scada mqtt_scada

echo "=== $(date '+%F %T') deploy done -> $(git rev-parse --short HEAD) ==="
