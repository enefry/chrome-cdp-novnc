FROM debian:trixie-slim

ARG TARGETARCH

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1
ENV SCREEN_WIDTH=1280
ENV SCREEN_HEIGHT=800
ENV XDG_RUNTIME_DIR=/tmp/runtime-chromeuser
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/local/bin/chrome-bin
ENV NOVNC_START_PAGE=vnc.html
ENV NOVNC_AUTOCONNECT=1
ENV NOVNC_RESIZE=remote
ENV NOVNC_PATH=websockify

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg procps supervisor tini \
    xvfb x11vnc fluxbox novnc websockify socat \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 \
    fonts-wqy-microhei python3 python3-requests \
    && if [ "${TARGETARCH}" = "amd64" ]; then \
        install -d -m 0755 /etc/apt/keyrings; \
        curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg; \
        echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list; \
        apt-get update; \
        apt-get install -y --no-install-recommends google-chrome-stable; \
      else \
        apt-get install -y --no-install-recommends chromium; \
      fi \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r chromeuser && useradd -r -m -g chromeuser -G audio,video chromeuser

RUN mkdir -p /data/chrome-profile /app /var/log/supervisor /var/run/supervisor "${XDG_RUNTIME_DIR}" \
    && chown -R chromeuser:chromeuser /data/chrome-profile /app /var/log/supervisor /var/run/supervisor "${XDG_RUNTIME_DIR}" \
    && chmod 0700 "${XDG_RUNTIME_DIR}"

VOLUME /data/chrome-profile

EXPOSE 6080 9222 9223

COPY config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY config/fluxbox-init /app/config/fluxbox-init
COPY config/fluxbox-apps /app/config/fluxbox-apps
COPY scripts/chrome_monitor.py /app/scripts/chrome_monitor.py
COPY scripts/start.sh /app/start.sh
COPY bin/fbsetbg /usr/local/bin/fbsetbg
COPY bin/chrome-bin.sh /usr/local/bin/chrome-bin

RUN chown chromeuser:chromeuser /app/config/fluxbox-init \
    /app/config/fluxbox-apps \
    /app/scripts/chrome_monitor.py \
    && chmod +x /app/start.sh /usr/local/bin/chrome-bin /usr/local/bin/fbsetbg

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/start.sh"]
