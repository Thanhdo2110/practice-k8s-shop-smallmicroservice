# build stage
FROM node:18.18-alpine as build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build


# run stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# FIX: dua config nginx vao image -> co try_files /index.html cho React Router (F5 khong 404)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
