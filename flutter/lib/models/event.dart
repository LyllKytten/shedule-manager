import '../utils/format.dart';

/// weekdays = Mon–Fri, weekends = Sat–Sun, cycle = N days on / M days off (e.g. 5:2).
enum RepeatType { none, daily, weekly, custom, weekdays, weekends, cycle }

class Event {
  final int id;
  final String title;
  final DateTime date;
  final String startTime; // HH:MM
  final String endTime; // HH:MM
  final int durationMinutes;
  final bool needsTravelTime;
  final String? seriesId;
  final String? repeatType;
  final int? repeatIntervalDays;
  final int? repeatDaysOn;
  final int? repeatDaysOff;
  final bool seriesInfinite;

  Event({
    required this.id,
    required this.title,
    required this.date,
    required this.startTime,
    required this.endTime,
    required this.durationMinutes,
    required this.needsTravelTime,
    this.seriesId,
    this.repeatType,
    this.repeatIntervalDays,
    this.repeatDaysOn,
    this.repeatDaysOff,
    this.seriesInfinite = false,
  });

  bool get isRecurring => seriesId != null;

  /// Short label of the repeat pattern, e.g. "daily", "Mon–Fri", "5:2".
  String get repeatLabel => switch (repeatType) {
        'daily' => 'daily',
        'weekly' => 'weekly',
        'custom' => 'every ${repeatIntervalDays ?? '?'} days',
        'weekdays' => 'Mon–Fri',
        'weekends' => 'Sat–Sun',
        'cycle' => '${repeatDaysOn ?? '?'}:${repeatDaysOff ?? '?'}',
        _ => 'series',
      };

  factory Event.fromJson(Map<String, dynamic> j) => Event(
        id: j['id'] as int,
        title: j['title'] as String,
        date: DateTime.parse(j['date'] as String),
        startTime: j['start_time'] as String,
        endTime: j['end_time'] as String,
        durationMinutes: j['duration_minutes'] as int,
        needsTravelTime: j['needs_travel_time'] as bool,
        seriesId: j['series_id'] as String?,
        repeatType: j['repeat_type'] as String?,
        repeatIntervalDays: j['repeat_interval_days'] as int?,
        repeatDaysOn: j['repeat_days_on'] as int?,
        repeatDaysOff: j['repeat_days_off'] as int?,
        seriesInfinite: (j['series_infinite'] as bool?) ?? false,
      );
}

/// Payload for creating one event or a series.
class NewEvent {
  final String title;
  final DateTime date;
  final String startTime;
  final int durationMinutes;
  final bool needsTravelTime;
  final RepeatType repeat;
  final int? intervalDays;

  /// Shift cycle: days with the event, then days without (only for [RepeatType.cycle]).
  final int? daysOn;
  final int? daysOff;

  /// Occurrences including the first one; null = infinite (only with repeat).
  final int? occurrences;

  NewEvent({
    required this.title,
    required this.date,
    required this.startTime,
    required this.durationMinutes,
    this.needsTravelTime = false,
    this.repeat = RepeatType.none,
    this.intervalDays,
    this.daysOn,
    this.daysOff,
    this.occurrences = 1,
  });

  Map<String, dynamic> toJson() => {
        'title': title,
        'date': apiDate(date),
        'start_time': startTime,
        'duration_minutes': durationMinutes,
        'needs_travel_time': needsTravelTime,
        'repeat_type': repeat == RepeatType.none ? null : repeat.name,
        'repeat_interval_days': repeat == RepeatType.custom ? intervalDays : null,
        'repeat_days_on': repeat == RepeatType.cycle ? daysOn : null,
        'repeat_days_off': repeat == RepeatType.cycle ? daysOff : null,
        'occurrences': repeat == RepeatType.none ? 1 : occurrences,
      };
}

class FreeSlot {
  final String start;
  final String end;
  FreeSlot(this.start, this.end);

  factory FreeSlot.fromJson(Map<String, dynamic> j) =>
      FreeSlot(j['start'] as String, j['end'] as String);
}

/// Free slots of one day (an item of GET /events/free/week).
class DayFreeSlots {
  final DateTime date;
  final List<FreeSlot> slots;
  DayFreeSlots(this.date, this.slots);

  factory DayFreeSlots.fromJson(Map<String, dynamic> j) => DayFreeSlots(
        DateTime.parse(j['date'] as String),
        (j['slots'] as List).map((e) => FreeSlot.fromJson(e)).toList(),
      );
}
