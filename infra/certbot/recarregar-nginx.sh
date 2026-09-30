#!/bin/sh

# Hook executado pelo Certbot após a renovação de um certificado.
docker exec evolync_nginx nginx -s reload
