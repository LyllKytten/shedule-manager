/// Backend base URL. Override at build time:
///   flutter run --dart-define=API_URL=http://192.168.1.10:8000
const String defaultApiUrl =
    String.fromEnvironment('API_URL', defaultValue: 'http://localhost:8000');
