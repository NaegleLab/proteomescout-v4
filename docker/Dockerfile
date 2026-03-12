FROM python:3.8-buster
LABEL maintainer="rkc7h@virginia.edu"
ENV APP_LOC /proteome_scout-3
RUN mkdir -p /root/.aws && \
    mkdir -p /home/.aws && \
    mkdir -p $APP_LOC

WORKDIR $APP_LOC
ADD ./requirements.txt .
RUN pip3 install -r requirements.txt \
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    && apt-get clean \
    && apt-get auto-remove -y \
    && rm -rf /var/cache/apt/* \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* && \
    echo "daemon off;" >> /etc/nginx/nginx.conf
RUN mkdir -p logs
EXPOSE 5000
ENV FLASK_APP app/__init__.py
ENV FLASK_DEBUG 0
ADD ./nginx_app.conf /etc/nginx/sites-available/default
ADD ./supervisor_app.conf /etc/supervisor/conf.d/supervisor_app.conf
ADD ./supervisor_app.conf /etc/supervisor/supervisord.conf
ADD ./. .
CMD ["supervisord"]
