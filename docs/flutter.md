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

## Commands

```bash
flutter pub get
flutter analyze
flutter test
flutter run -d chrome --dart-define=API_URL=http://localhost:8000
```
