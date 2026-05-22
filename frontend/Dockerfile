FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_API_BASE_URL=/api
ARG VITE_PUBLIC_BASE_URL=https://your-domain.com
ARG VITE_XHS_SDK_URL=https://fe-static.xhscdn.com/agora/lib/v2/xhs-1.0.0.js

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_PUBLIC_BASE_URL=$VITE_PUBLIC_BASE_URL
ENV VITE_XHS_SDK_URL=$VITE_XHS_SDK_URL

COPY package.json .
RUN npm install

COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
