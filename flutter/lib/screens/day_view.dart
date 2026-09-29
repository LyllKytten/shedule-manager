import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/event.dart';
import '../state/auth_state.dart';
import '../utils/format.dart';
import '../widgets/common.dart';
import '../widgets/event_tile.dart';

/// Events for one selected day plus the free time slots for that day.
class DayView extends StatefulWidget {
  const DayView({super.key});

  @override
  State<DayView> createState() => _DayViewState();
}

class _DayViewState extends State<DayView> {
  DateTime _day = dateOnly(DateTime.now());
  late Future<(List<Event>, List<FreeSlot>)> _data;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    final api = context.read<AuthState>().api;
    setState(() {
      _data = () async {
        final events = await api.events(_day);
        final free = await api.freeSlots(_day);
        return (events, free);
      }();
    });
  }

  void _shift(int days) {
    _day = _day.add(Duration(days: days));
    _load();
  }

  Future<void> _pick() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _day,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (picked != null) {
      _day = dateOnly(picked);
      _load();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isToday = _day == dateOnly(DateTime.now());
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Row(
            children: [
              IconButton(icon: const Icon(Icons.chevron_left), onPressed: () => _shift(-1)),
              Expanded(
                child: TextButton.icon(
                  onPressed: _pick,
                  icon: const Icon(Icons.calendar_today, size: 18),
                  label: Text('${weekdayDate(_day)}${isToday ? '  (today)' : ''}'),
                ),
              ),
              IconButton(icon: const Icon(Icons.chevron_right), onPressed: () => _shift(1)),
            ],
          ),
        ),
        Expanded(
          child: FutureBuilder(
            future: _data,
            builder: (context, snap) {
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
              final (events, free) = snap.data!;
              return RefreshIndicator(
                onRefresh: () async => _load(),
                child: ListView(
                  padding: const EdgeInsets.only(bottom: 96),
                  children: [
                    if (events.isEmpty)
                      const EmptyState(icon: Icons.event_available, text: 'No events on this day')
                    else
                      ...events.map((e) => EventTile(event: e, onChanged: _load)),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
                      child: Text('Free time', style: Theme.of(context).textTheme.titleMedium),
                    ),
                    if (free.isEmpty)
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 16),
                        child: Text('No free time on this day'),
                      )
                    else
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        child: Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: free
                              .map((s) => Chip(
                                    avatar: const Icon(Icons.circle, size: 10, color: Colors.green),
                                    label: Text('${s.start} – ${s.end}'),
                                  ))
                              .toList(),
                        ),
                      ),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}
