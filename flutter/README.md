# Schedule Manager — Flutter app

Graphical client for the [backend](../backend). Full docs: [../docs/flutter.md](../docs/flutter.md).

```bash
flutter pub get
flutter run --dart-define=API_URL=http://localhost:8000
```

Docker (web build + nginx on :8080):

```bash
API_URL=http://localhost:8000 docker compose up -d --build
```
