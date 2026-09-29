# ---- build stage: compile the Flutter web app ----
FROM ghcr.io/cirruslabs/flutter:stable AS build

ARG API_URL=http://35.207.134.118:8000
WORKDIR /app
COPY pubspec.yaml pubspec.lock ./
RUN flutter pub get
COPY . .
RUN flutter build web --release --dart-define=API_URL=${API_URL}

# ---- runtime stage: serve static files with nginx ----
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build/web /usr/share/nginx/html
EXPOSE 80
