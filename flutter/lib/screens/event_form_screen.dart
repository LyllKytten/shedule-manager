import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/event.dart';
import '../state/auth_state.dart';
import '../utils/format.dart';
import '../widgets/common.dart';

/// Create a new event (with optional repetition) or edit one occurrence of an existing one.
/// Pops `true` when something was saved.
class EventFormScreen extends StatefulWidget {
  final Event? existing;
  const EventFormScreen({super.key, this.existing});

  @override
  State<EventFormScreen> createState() => _EventFormScreenState();
}

class _EventFormScreenState extends State<EventFormScreen> {
  final _form = GlobalKey<FormState>();
  late final TextEditingController _title;
  late final TextEditingController _duration;
  final _interval = TextEditingController(text: '2');
  final _customOcc = TextEditingController(text: '10');

  late DateTime _date;
  late TimeOfDay _time;
  late bool _travel;
  RepeatType _repeat = RepeatType.none;
  // 4, 8, 12, -1 = custom, 0 = infinite
  int _occChoice = 4;
  bool _busy = false;

  bool get _editing => widget.existing != null;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    _title = TextEditingController(text: e?.title ?? '');
    _duration = TextEditingController(text: '${e?.durationMinutes ?? 60}');
    _date = e?.date ?? dateOnly(DateTime.now());
    _time = e != null ? parseHhmm(e.startTime) : const TimeOfDay(hour: 9, minute: 0);
    _travel = e?.needsTravelTime ?? true;
  }

  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    setState(() => _busy = true);
    final api = context.read<AuthState>().api;
    try {
      if (_editing) {
        await api.updateEvent(widget.existing!.id, {
          'title': _title.text.trim(),
          'date': apiDate(_date),
          'start_time': hhmm(_time),
          'duration_minutes': int.parse(_duration.text),
          'needs_travel_time': _travel,
        });
      } else {
        int? occurrences = 1;
        if (_repeat != RepeatType.none) {
          occurrences = switch (_occChoice) {
            0 => null,
            -1 => int.parse(_customOcc.text),
            _ => _occChoice,
          };
        }
        await api.createEvent(NewEvent(
          title: _title.text.trim(),
          date: _date,
          startTime: hhmm(_time),
          durationMinutes: int.parse(_duration.text),
          needsTravelTime: _travel,
          repeat: _repeat,
          intervalDays: _repeat == RepeatType.custom ? int.parse(_interval.text) : null,
          occurrences: occurrences,
        ));
      }
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) showError(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  String? _positiveInt(String? v) {
    final n = int.tryParse(v ?? '');
    return (n == null || n <= 0) ? 'Enter a positive number' : null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_editing ? 'Edit event' : 'New event'),
        actions: [
          TextButton(onPressed: _busy ? null : _save, child: const Text('Save')),
        ],
      ),
      body: Form(
        key: _form,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (_editing && widget.existing!.isRecurring)
              const Card(
                child: ListTile(
                  leading: Icon(Icons.info_outline),
                  title: Text('Only this occurrence will be changed'),
                ),
              ),
            TextFormField(
              controller: _title,
              decoration: const InputDecoration(labelText: 'Title', border: OutlineInputBorder()),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.calendar_today),
                    label: Text(humanDate(_date)),
                    onPressed: () async {
                      final d = await showDatePicker(
                        context: context,
                        initialDate: _date,
                        firstDate: DateTime(2000),
                        lastDate: DateTime(2100),
                      );
                      if (d != null) setState(() => _date = dateOnly(d));
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.schedule),
                    label: Text(hhmm(_time)),
                    onPressed: () async {
                      final t = await showTimePicker(
                        context: context,
                        initialTime: _time,
                        builder: (ctx, child) => MediaQuery(
                          data: MediaQuery.of(ctx).copyWith(alwaysUse24HourFormat: true),
                          child: child!,
                        ),
                      );
                      if (t != null) setState(() => _time = t);
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _duration,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Duration (minutes)',
                border: OutlineInputBorder(),
              ),
              validator: _positiveInt,
            ),
            const SizedBox(height: 4),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('🚗 Travel time after this event'),
              subtitle: const Text('Reserve travel time before the next free slot'),
              value: _travel,
              onChanged: (v) => setState(() => _travel = v),
            ),
            if (!_editing) ...[
              const Divider(height: 32),
              Text('Repeat', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              SegmentedButton<RepeatType>(
                segments: const [
                  ButtonSegment(value: RepeatType.none, label: Text('No')),
                  ButtonSegment(value: RepeatType.daily, label: Text('Daily')),
                  ButtonSegment(value: RepeatType.weekly, label: Text('Weekly')),
                  ButtonSegment(value: RepeatType.custom, label: Text('Every N')),
                ],
                selected: {_repeat},
                onSelectionChanged: (s) => setState(() => _repeat = s.first),
              ),
              if (_repeat == RepeatType.custom) ...[
                const SizedBox(height: 12),
                TextFormField(
                  controller: _interval,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Every N days',
                    border: OutlineInputBorder(),
                  ),
                  validator: _positiveInt,
                ),
              ],
              if (_repeat != RepeatType.none) ...[
                const SizedBox(height: 16),
                Text('How many times (including the first)'),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: [
                    for (final (v, label) in [(4, '4'), (8, '8'), (12, '12'), (0, '♾ Forever'), (-1, 'Custom')])
                      ChoiceChip(
                        label: Text(label),
                        selected: _occChoice == v,
                        onSelected: (_) => setState(() => _occChoice = v),
                      ),
                  ],
                ),
                if (_occChoice == -1) ...[
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _customOcc,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Occurrences',
                      border: OutlineInputBorder(),
                    ),
                    validator: _positiveInt,
                  ),
                ],
              ],
            ],
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _busy ? null : _save,
              child: const Padding(
                padding: EdgeInsets.symmetric(vertical: 12),
                child: Text('Save'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
