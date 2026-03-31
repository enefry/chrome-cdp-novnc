#!/bin/sh
set -eu

rm -f /data/chrome-profile/SingletonCookie \
    /data/chrome-profile/SingletonLock \
    /data/chrome-profile/SingletonSocket

if [ -x /usr/bin/google-chrome-stable ]; then
    exec /usr/bin/google-chrome-stable "$@"
fi

exec /usr/bin/chromium "$@"
