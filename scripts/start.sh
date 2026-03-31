#!/bin/sh
set -eu

mkdir -p /data/chrome-profile /var/log/supervisor /var/run/supervisor "${XDG_RUNTIME_DIR}"
mkdir -p /home/chromeuser/.fluxbox
chown -R chromeuser:chromeuser /data/chrome-profile /var/log/supervisor /var/run/supervisor "${XDG_RUNTIME_DIR}"
chmod 0700 "${XDG_RUNTIME_DIR}"
cp /app/config/fluxbox-init /home/chromeuser/.fluxbox/init
cp /app/config/fluxbox-apps /home/chromeuser/.fluxbox/apps
chown chromeuser:chromeuser /home/chromeuser/.fluxbox/init
chown chromeuser:chromeuser /home/chromeuser/.fluxbox/apps

NOVNC_TARGET="./${NOVNC_START_PAGE:-vnc.html}?autoconnect=${NOVNC_AUTOCONNECT:-1}&resize=${NOVNC_RESIZE:-remote}&path=${NOVNC_PATH:-websockify}"
cat > /usr/share/novnc/index.html <<EOF
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Redirecting to noVNC</title>
  <meta http-equiv="refresh" content="0; url=${NOVNC_TARGET}">
</head>
<body>
  <p>Redirecting to <a id="novnc-link" href="${NOVNC_TARGET}">noVNC</a>...</p>
  <script>
    window.location.replace(document.getElementById("novnc-link").href);
  </script>
</body>
</html>
EOF

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
