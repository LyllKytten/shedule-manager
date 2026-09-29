# Schedule Manager — Flutter app

Graphical client for the [backend](../backend). Full docs: [../docs/flutter.md](../docs/flutter.md).

By default the app talks to the production backend at `http://35.207.134.118:8000`
(Google Cloud VM). To use a backend running on your machine instead:

```bash
flutter pub get
flutter run --dart-define=API_URL=http://localhost:8000
```

Release builds (output in `dist/`, run `./build.sh` for all options):

```bash
./build.sh apk-split   # Android
./build.sh ios         # iPhone (on a Mac)
./build.sh macos       # macOS  (on a Mac)
```

Docker (web build + nginx on :8080):

```bash
docker compose up -d --build   # API_URL=... to point at another backend
```
