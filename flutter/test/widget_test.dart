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
}
