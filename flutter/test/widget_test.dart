import 'package:flutter_test/flutter_test.dart';
import 'package:schedule_manager/models/event.dart';
import 'package:schedule_manager/utils/format.dart';

void main() {
  test('Event.fromJson parses backend payload', () {
    final e = Event.fromJson({
      'id': 1,
      'title': 'Gym',
      'date': '2026-10-01',
      'start_time': '10:00',
      'end_time': '11:00',
      'duration_minutes': 60,
      'needs_travel_time': true,
      'series_id': 'abc',
      'repeat_type': 'weekly',
      'repeat_interval_days': 7,
      'series_infinite': false,
    });
    expect(e.isRecurring, isTrue);
    expect(humanDate(e.date), '01.10.2026');
  });

  test('NewEvent.toJson encodes infinite custom series', () {
    final json = NewEvent(
      title: 'X',
      date: DateTime(2026, 10, 1),
      startTime: '09:00',
      durationMinutes: 30,
      needsTravelTime: false,
      repeat: RepeatType.custom,
      intervalDays: 3,
      occurrences: null,
    ).toJson();
    expect(json['repeat_type'], 'custom');
    expect(json['repeat_interval_days'], 3);
    expect(json['occurrences'], isNull);
    expect(json['date'], '2026-10-01');
  });

  test('NewEvent.toJson encodes a 5:2 shift cycle, travel off by default', () {
    final json = NewEvent(
      title: 'Shift',
      date: DateTime(2026, 10, 1),
      startTime: '08:00',
      durationMinutes: 480,
      repeat: RepeatType.cycle,
      daysOn: 5,
      daysOff: 2,
      occurrences: 10,
    ).toJson();
    expect(json['repeat_type'], 'cycle');
    expect(json['repeat_days_on'], 5);
    expect(json['repeat_days_off'], 2);
    expect(json['repeat_interval_days'], isNull);
    expect(json['needs_travel_time'], isFalse);
  });

  test('Event.repeatLabel describes weekday and cycle series', () {
    Event make(Map<String, dynamic> extra) => Event.fromJson({
          'id': 1, 'title': 'X', 'date': '2026-10-01', 'start_time': '08:00',
          'end_time': '09:00', 'duration_minutes': 60, 'needs_travel_time': false,
          'series_id': 's', 'repeat_interval_days': null, 'series_infinite': false,
          ...extra,
        });
    expect(make({'repeat_type': 'weekdays'}).repeatLabel, 'Mon–Fri');
    expect(make({'repeat_type': 'cycle', 'repeat_days_on': 3, 'repeat_days_off': 2}).repeatLabel, '3:2');
  });
}
