/// Backend base URL. Defaults to the production server on the Google Cloud VM.
/// Override at build time, e.g. for a backend running on this machine:
///   flutter run --dart-define=API_URL=http://localhost:8000
const String defaultApiUrl =
    String.fromEnvironment('API_URL', defaultValue: 'http://35.207.134.118:8000');
