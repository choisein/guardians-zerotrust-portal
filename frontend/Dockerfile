FROM nginx:alpine

# 모든 파일 복사
COPY . /usr/share/nginx/html

# nginx가 templates/ 폴더를 루트로 보도록 설정
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html/templates;\n\
    index login.html;\n\
    location /css/ {\n\
        alias /usr/share/nginx/html/css/;\n\
    }\n\
    location /js/ {\n\
        alias /usr/share/nginx/html/js/;\n\
    }\n\
    location / {\n\
        try_files $uri $uri/ =404;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

# 80 포트 노출
EXPOSE 80

# nginx 실행
CMD ["nginx", "-g", "daemon off;"]
