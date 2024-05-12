FROM python:3.12.3-alpine3.19 as builder
RUN pip install pyinstaller install telethon loguru json5
RUN apk add binutils
COPY ./telegram.py ./telegram.py
RUN pyinstaller --onefile telegram.py
RUN mkdir /emptydir

FROM scratch as merger
COPY --from=builder ./dist/telegram /
COPY --from=builder /lib/libz.so.1 /lib/ld-musl-x86_64.so.1 /lib/
COPY --from=builder /emptydir /tmp

FROM scratch as runner
ENV LD_LIBRARY_PATH=/
ENTRYPOINT [ "/telegram" ]
COPY --from=merger / /
