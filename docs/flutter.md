# Flutter app

A graphical version of the Telegram bot. Talks to the backend over REST.
Packages: `http`, `provider`, `shared_preferences`, `intl`. Material 3,
light/dark theme follows the system.

## Structure

```
flutter/lib/
├── main.dart                  App root; shows Login or Home depending on AuthState
├── config.dart                defaultApiUrl (from --dart-define=API_URL)
├── models/
│   ├── event.dart             Event, NewEvent (create payload), RepeatType, FreeSlot
│   ├── user.dart              User
│   └── user_settings.dart     UserSettings
├── services/api_client.dart   All HTTP calls; ApiException; 401 → onUnauthorized
├── state/auth_state.dart      ChangeNotifier: token, current user, server URL (persisted)
├── utils/format.dart          Date/time formatting and parsing helpers
├── widgets/
│   ├── common.dart            showError / showInfo snackbars, EmptyState
│   └── event_tile.dart        Event card with edit + delete (one / whole series)
└── screens/
    ├── login_screen.dart      Sign in / register, server URL dialog
    ├── home_screen.dart       Bottom navigation: Day / Week / Settings, FAB "Event"
    ├── day_view.dart          Events of a day + free-time chips, day navigation
    ├── week_view.dart         7 days, week navigation; Plans / Free time switch
    ├── event_form_screen.dart Create (with repeat options) or edit one occurrence
    ├── settings_screen.dart   Travel time, working hours, password, admin, sign out
    └── admin_screen.dart      Superuser: create/enable/disable/promote/delete users
```

## State

`AuthState` is the only global state (provided at the root). Screens load their
own data through `context.read<AuthState>().api` and reload after changes; the
home screen bumps a key after adding an event so the visible tab refetches.

## Backend URL

Default: `http://35.207.134.118:8000` (the Google Cloud VM), set in
`lib/config.dart`. Override per build with `--dart-define=API_URL=...`, or at
runtime via the server address on the login screen (saved on the device and
used instead of the default from then on).

## Building releases — `build.sh`

```bash
cd flutter
./build.sh apk-split     # Android (phones: dist/*-arm64-v8a.apk)
./build.sh ios           # iPhone .ipa      (on a Mac with Xcode)
./build.sh macos         # macOS app .zip   (on a Mac with Xcode)
./build.sh all           # everything this OS can build
```

Output goes to `flutter/dist/`. Run `./build.sh` without arguments for all
targets. `API_URL`, `BUILD_NAME` and `BUILD_NUMBER` override the backend URL and
version, e.g. `BUILD_NUMBER=2 ./build.sh apk` (Android/iOS only install an
update when the build number is higher).

### Apple platforms

Needs a Mac with Xcode and CocoaPods (`brew install cocoapods`).

- **iOS signing:** open `ios/Runner.xcworkspace` in Xcode → *Runner* →
  *Signing & Capabilities* → choose your Team (a free Apple ID works for
  installing on your own iPhone). `flutter run --release` with the phone
  plugged in installs it directly.
- **http://** is allowed via `NSAppTransportSecurity` in both `Info.plist`
  files, because the backend has no HTTPS yet. Remove it once it does.
- **macOS sandbox:** `com.apple.security.network.client` in the
  `.entitlements` files lets the app connect to the backend.

## Commands

```bash
flutter pub get
flutter analyze
flutter test
flutter run -d chrome --dart-define=API_URL=http://localhost:8000
```
