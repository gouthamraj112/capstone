FROM node:18-alpine
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --silent || npm install --silent
COPY frontend /app
RUN npm run build

FROM nginx:stable-alpine
COPY --from=0 /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
