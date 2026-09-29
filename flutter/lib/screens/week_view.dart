import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/event.dart';
import '../state/auth_state.dart';
import '../utils/format.dart';
import '../widgets/common.dart';
import '../widgets/event_tile.dart';

enum WeekMode { plans, free }

/// 7 days starting from the selected date: either the events grouped by day
/// ("Plans") or the free time slots of each day ("Free time").
class WeekView extends StatefulWidget {
  const WeekView({super.key});

  @override
  State<WeekView> createState() => _WeekViewState();
}

class _WeekViewState extends State<WeekView> {
  // Static so the chosen mode survives switching bottom-navigation tabs.
  static WeekMode _mode = WeekMode.plans;

  DateTime _start = dateOnly(DateTime.now());
  late Future<List<Event>> _plans;
  late Future<List<DayFreeSlots>> _free;

  DateTime get _end => _start.add(const Duration(days: 6));

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    final api = context.read<AuthState>().api;
    setState(() {
      if (_mode == WeekMode.plans) {
        _plans = api.events(_start, _end);
      } else {
        _free = api.freeWeek(_start);
      }
    });
  }

  void _shift(int days) {
    _start = _start.add(Duration(days: days));
    _load();
  }

  void _setMode(WeekMode mode) {
    _mode = mode;
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Row(
            children: [
              IconButton(icon: const Icon(Icons.chevron_left), onPressed: () => _shift(-7)),
              Expanded(
                child: Text(
                  '${humanDate(_start)} – ${humanDate(_end)}',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.titleSmall,
                ),
              ),
              IconButton(icon: const Icon(Icons.chevron_right), onPressed: () => _shift(7)),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
          child: SegmentedButton<WeekMode>(
            segments: const [
              ButtonSegment(value: WeekMode.plans, icon: Icon(Icons.event_note), label: Text('Plans')),
              ButtonSegment(value: WeekMode.free, icon: Icon(Icons.hourglass_empty), label: Text('Free time')),
            ],
            selected: {_mode},
            onSelectionChanged: (s) => _setMode(s.first),
          ),
        ),
        Expanded(child: _mode == WeekMode.plans ? _buildPlans() : _buildFree()),
      ],
    );
  }

  Widget _loading<T>(AsyncSnapshot<T> snap, Widget Function(T data) builder) {
    if (snap.connectionState != ConnectionState.done) {
      return const Center(child: CircularProgressIndicator());
    }
    if (snap.hasError) {
      return Center(
        child: TextButton.icon(
          onPressed: _load,
          icon: const Icon(Icons.refresh),
          label: Text('${snap.error}\nTap to retry', textAlign: TextAlign.center),
        ),
      );
    }
    return RefreshIndicator(onRefresh: () async => _load(), child: builder(snap.data as T));
  }

  Widget _dayHeader(DateTime day, {String? trailing}) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
      child: Row(
        children: [
          Expanded(
            child: Text(
              weekdayDate(day),
              style: theme.textTheme.titleMedium?.copyWith(color: theme.colorScheme.primary),
            ),
          ),
          if (trailing != null)
            Text(trailing, style: TextStyle(color: theme.colorScheme.outline)),
        ],
      ),
    );
  }

  Widget _buildPlans() {
    return FutureBuilder(
      future: _plans,
      builder: (context, snap) => _loading(snap, (List<Event> events) {
        if (events.isEmpty) {
          return ListView(children: const [
            EmptyState(icon: Icons.event_busy, text: 'No events this week'),
          ]);
        }
        final byDay = <DateTime, List<Event>>{};
        for (final e in events) {
          byDay.putIfAbsent(dateOnly(e.date), () => []).add(e);
        }
        return ListView(
          padding: const EdgeInsets.only(bottom: 96),
          children: [
            for (final entry in byDay.entries) ...[
              _dayHeader(entry.key),
              ...entry.value.map((e) => EventTile(event: e, onChanged: _load)),
            ],
          ],
        );
      }),
    );
  }

  Widget _buildFree() {
    return FutureBuilder(
      future: _free,
      builder: (context, snap) => _loading(snap, (List<DayFreeSlots> days) {
        return ListView(
          padding: const EdgeInsets.only(bottom: 96),
          children: [
            for (final day in days) ...[
              _dayHeader(day.date, trailing: _totalLabel(day.slots)),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: day.slots.isEmpty
                    ? const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 4, vertical: 8),
                        child: Text('No free time'),
                      )
                    : Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: day.slots
                            .map((s) => Chip(
                                  avatar: const Icon(Icons.circle, size: 10, color: Colors.green),
                                  label: Text('${s.start} – ${s.end}'),
                                ))
                            .toList(),
                      ),
              ),
            ],
          ],
        );
      }),
    );
  }

  /// "5 h 30 min free" — total length of the day's slots.
  String _totalLabel(List<FreeSlot> slots) {
    var minutes = 0;
    for (final s in slots) {
      final a = parseHhmm(s.start), b = parseHhmm(s.end);
      var diff = (b.hour * 60 + b.minute) - (a.hour * 60 + a.minute);
      if (diff <= 0) diff += 24 * 60; // slot ends after midnight
      minutes += diff;
    }
    if (minutes == 0) return 'busy';
    final h = minutes ~/ 60, m = minutes % 60;
    return '${h > 0 ? '$h h ' : ''}${m > 0 ? '$m min ' : ''}free';
  }
}
