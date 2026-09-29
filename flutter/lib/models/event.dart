import '../utils/format.dart';

enum RepeatType { none, daily, weekly, custom }

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
    this.seriesInfinite = false,
  });

  bool get isRecurring => seriesId != null;

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

  /// Occurrences including the first one; null = infinite (only with repeat).
  final int? occurrences;

  NewEvent({
    required this.title,
    required this.date,
    required this.startTime,
    required this.durationMinutes,
    required this.needsTravelTime,
    this.repeat = RepeatType.none,
    this.intervalDays,
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
