FROM python:3.12.3-alpine3.19 as builder
RUN pip install pyinstaller telethon loguru json5 python-dateutil
RUN apk add binutils
COPY ./telegram.py ./telegram.py
RUN pyinstaller telegram.py
RUN mkdir /emptydir

FROM scratch as merger
COPY --from=builder ./dist/telegram /kt.pizza
COPY --from=builder /lib/libz.so.1 /lib/ld-musl-x86_64.so.1 /lib/

FROM scratch as runner
ENTRYPOINT [ "/kt.pizza/telegram" ]
USER 1000
COPY --from=merger / /
