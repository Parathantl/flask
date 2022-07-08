# latest nginx
FROM nginx:1.21.0-alpine
# copy custom configuration file
COPY proxy.conf /etc/nginx/conf.d/default.conf
# expose server port
EXPOSE 80
EXPOSE 443

# VOLUME /etc/nginx/certs

CMD [ "nginx", "-g", "daemon off;" ]

