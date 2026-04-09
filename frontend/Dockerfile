FROM nginx:alpine

# 모든 정적 파일을 nginx 웹 루트에 복사
COPY . /usr/share/nginx/html

# 80 포트 노출
EXPOSE 80

# nginx 실행
CMD ["nginx", "-g", "daemon off;"]
