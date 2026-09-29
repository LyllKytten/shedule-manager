class UserSettings {
  final int travelTimeMinutes;
  final String dayStart;
  final String dayEnd;

  UserSettings({
    required this.travelTimeMinutes,
    required this.dayStart,
    required this.dayEnd,
  });

  factory UserSettings.fromJson(Map<String, dynamic> j) => UserSettings(
        travelTimeMinutes: j['travel_time_minutes'] as int,
        dayStart: j['day_start'] as String,
        dayEnd: j['day_end'] as String,
      );
}
