FROM postgres:16

RUN apt-get update && apt-get install -y locales
RUN sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

ENV LANG=ru_RU.UTF-8 LC_COLLATE=ru_RU.UTF-8 LC_CTYPE=ru_RU.UTF-8
