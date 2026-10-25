# ---- dev: used by docker-compose (hot reload, src bind-mounted) ----
FROM node:22-alpine AS dev

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

COPY . .
RUN npx nuxt prepare

EXPOSE 3000
CMD ["npm", "run", "dev"]

# ---- build: static SPA bundle (ssr: false) ----
FROM dev AS build
# NUXT_PUBLIC_* are inlined at build time
ARG NUXT_PUBLIC_API_BASE
ENV NUXT_PUBLIC_API_BASE=${NUXT_PUBLIC_API_BASE}
RUN npm run generate

# ---- prod: serve the generated SPA ----
FROM nginx:1.27-alpine AS prod
COPY --from=build /app/.output/public /usr/share/nginx/html
RUN printf 'server {\n  listen 80;\n  root /usr/share/nginx/html;\n  location / { try_files $uri $uri/ /index.html; }\n}\n' > /etc/nginx/conf.d/default.conf
EXPOSE 80
