FROM lscr.io/linuxserver/baseimage-alpine:3.23

RUN apk add --no-cache python3 python3-dev py3-pip;chown -R abc:abc /app
COPY --chown=abc:abc *.py /app
COPY --chown=abc:abc requirements.txt /app

USER abc

ENV VIRTUAL_ENV=/app/.venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip3 install -r /app/requirements.txt
