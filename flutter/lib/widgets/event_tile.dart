import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/event.dart';
import '../screens/event_form_screen.dart';
import '../state/auth_state.dart';
import 'common.dart';

/// A card for one event with edit / delete actions. Calls [onChanged] after a change.
class EventTile extends StatelessWidget {
  final Event event;
  final VoidCallback onChanged;

  const EventTile({super.key, required this.event, required this.onChanged});

  Future<void> _edit(BuildContext context) async {
    final changed = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => EventFormScreen(existing: event)),
    );
    if (changed == true) onChanged();
  }

  Future<void> _delete(BuildContext context) async {
    final api = context.read<AuthState>().api;
    String? choice;
    if (event.isRecurring) {
      choice = await showDialog<String>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Recurring event'),
          content: const Text('Delete only this occurrence or the whole series?'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            TextButton(onPressed: () => Navigator.pop(ctx, 'one'), child: const Text('Only this')),
            FilledButton(onPressed: () => Navigator.pop(ctx, 'series'), child: const Text('Whole series')),
          ],
        ),
      );
    } else {
      choice = await showDialog<String>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Delete event?'),
          content: Text(event.title),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            FilledButton(onPressed: () => Navigator.pop(ctx, 'one'), child: const Text('Delete')),
          ],
        ),
      );
    }
    if (choice == null) return;
    try {
      if (choice == 'series') {
        await api.deleteSeries(event.seriesId!);
      } else {
        await api.deleteEvent(event.id);
      }
      onChanged();
    } catch (e) {
      if (context.mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: ListTile(
        leading: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(event.startTime, style: const TextStyle(fontWeight: FontWeight.bold)),
            Text(event.endTime, style: TextStyle(color: scheme.outline, fontSize: 12)),
          ],
        ),
        title: Text(event.title),
        subtitle: Wrap(
          spacing: 8,
          children: [
            Text('${event.durationMinutes} min'),
            if (event.needsTravelTime) const Text('🚗 travel after'),
            if (event.isRecurring) Text('${event.seriesInfinite ? '♾' : '🔁'} ${event.repeatLabel}'),
          ],
        ),
        onTap: () => _edit(context),
        trailing: IconButton(
          icon: const Icon(Icons.delete_outline),
          tooltip: 'Delete',
          onPressed: () => _delete(context),
        ),
      ),
    );
  }
}
