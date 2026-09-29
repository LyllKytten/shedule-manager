import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

/// yyyy-MM-dd, the date format the backend expects.
String apiDate(DateTime d) => DateFormat('yyyy-MM-dd').format(d);

/// dd.MM.yyyy, the human-readable format used in the Telegram bot.
String humanDate(DateTime d) => DateFormat('dd.MM.yyyy').format(d);

String weekdayDate(DateTime d) => DateFormat('EEE, dd.MM').format(d);

String hhmm(TimeOfDay t) =>
    '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

TimeOfDay parseHhmm(String s) {
  final parts = s.split(':');
  return TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1]));
}

DateTime dateOnly(DateTime d) => DateTime(d.year, d.month, d.day);
