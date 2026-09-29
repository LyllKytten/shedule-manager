import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:provider/provider.dart';
import 'package:schedule_manager/models/user.dart';
import 'package:schedule_manager/screens/admin_screen.dart';
import 'package:schedule_manager/screens/day_view.dart';
import 'package:schedule_manager/screens/settings_screen.dart';
import 'package:schedule_manager/screens/week_view.dart';
import 'package:schedule_manager/state/auth_state.dart';

/// Fake backend: answers every endpoint the screens call.
final _backend = MockClient((req) async {
  final body = switch (req.url.path) {
    '/events' => [
        {
          'id': 1, 'title': 'Gym', 'date': req.url.queryParameters['start'],
          'start_time': '10:00', 'end_time': '11:00', 'duration_minutes': 60,
          'needs_travel_time': true, 'series_id': null, 'repeat_type': null,
          'repeat_interval_days': null, 'series_infinite': false,
        }
      ],
    '/events/free' => {
        'date': req.url.queryParameters['day'],
        'slots': [{'start': '11:30', 'end': '23:00'}],
      },
    '/events/free/week' => [
        for (var i = 1; i <= 7; i++)
          {
            'date': '2026-10-0$i',
            'slots': i == 2
                ? []
                : [
                    {'start': '08:00', 'end': '10:00'},
                    {'start': '11:30', 'end': '23:00'},
                  ],
          }
      ],
    '/settings' => {'travel_time_minutes': 30, 'day_start': '08:00', 'day_end': '23:00'},
    '/admin/users' => [
        {'id': 1, 'username': 'harak1r1', 'is_active': true, 'is_superuser': true, 'created_at': '2026-09-29T00:00:00Z'},
        {'id': 2, 'username': 'alice', 'is_active': true, 'is_superuser': false, 'created_at': '2026-09-29T00:00:00Z'},
      ],
    _ => throw StateError('unexpected request ${req.url}'),
  };
  return http.Response(jsonEncode(body), 200, headers: {'content-type': 'application/json'});
});

Future<void> _pumpScreen(WidgetTester tester, Widget screen) async {
  final auth = AuthState()
    ..api.token = 'test'
    ..user = User(id: 1, username: 'harak1r1', isActive: true, isSuperuser: true);
  await tester.pumpWidget(
    ChangeNotifierProvider.value(
      value: auth,
      child: MaterialApp(home: Scaffold(body: screen)),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  // Runs each test with the fake backend behind package:http's top-level functions.
  void screenTest(String name, Future<void> Function(WidgetTester) body) {
    testWidgets(name, (tester) => http.runWithClient(() => body(tester), () => _backend));
  }

  screenTest('Day view shows events and free time', (tester) async {
    await _pumpScreen(tester, const DayView());
    expect(tester.takeException(), isNull);
    expect(find.text('Gym'), findsOneWidget);
    expect(find.text('11:30 – 23:00'), findsOneWidget);
  });

  screenTest('Week view renders and navigates', (tester) async {
    await _pumpScreen(tester, const WeekView());
    expect(tester.takeException(), isNull);
    expect(find.text('Gym'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.chevron_right));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  screenTest('Week view switches to free time per day', (tester) async {
    await _pumpScreen(tester, const WeekView());
    await tester.tap(find.text('Free time'));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.text('Gym'), findsNothing);
    expect(find.text('08:00 – 10:00'), findsWidgets);
    expect(find.text('13 h 30 min free'), findsWidgets);
    expect(find.text('No free time'), findsOneWidget);
    expect(find.text('busy'), findsOneWidget);

    await tester.tap(find.text('Plans'));
    await tester.pumpAndSettle();
    expect(find.text('Gym'), findsOneWidget);
  });

  screenTest('Settings screen renders', (tester) async {
    await _pumpScreen(tester, const SettingsScreen());
    expect(tester.takeException(), isNull);
    expect(find.text('30 min'), findsOneWidget);
    expect(find.text('Manage users'), findsOneWidget);
  });

  screenTest('Admin screen lists users', (tester) async {
    await _pumpScreen(tester, const AdminScreen());
    expect(tester.takeException(), isNull);
    expect(find.text('harak1r1 (you)'), findsOneWidget);
    expect(find.text('alice'), findsOneWidget);
  });
}
