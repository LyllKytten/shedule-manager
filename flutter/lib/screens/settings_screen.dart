import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/user_settings.dart';
import '../state/auth_state.dart';
import '../utils/format.dart';
import '../widgets/common.dart';
import 'admin_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  UserSettings? _settings;
  Object? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final s = await context.read<AuthState>().api.settings();
      setState(() => _settings = s);
    } catch (e) {
      setState(() => _error = e);
    }
  }

  Future<void> _update(Map<String, dynamic> fields) async {
    try {
      final s = await context.read<AuthState>().api.updateSettings(fields);
      setState(() => _settings = s);
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Future<void> _editTravel() async {
    final ctrl = TextEditingController(text: '${_settings!.travelTimeMinutes}');
    final v = await showDialog<int>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Travel time (minutes)'),
        content: TextField(controller: ctrl, keyboardType: TextInputType.number, autofocus: true),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, int.tryParse(ctrl.text)),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    if (v != null && v >= 0) _update({'travel_time_minutes': v});
  }

  Future<void> _editTime(String field, String current) async {
    final t = await showTimePicker(
      context: context,
      initialTime: parseHhmm(current),
      builder: (ctx, child) => MediaQuery(
        data: MediaQuery.of(ctx).copyWith(alwaysUse24HourFormat: true),
        child: child!,
      ),
    );
    if (t != null) _update({field: hhmm(t)});
  }

  Future<void> _changePassword() async {
    final oldCtrl = TextEditingController();
    final newCtrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Change password'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: oldCtrl, obscureText: true, decoration: const InputDecoration(labelText: 'Current password')),
            TextField(controller: newCtrl, obscureText: true, decoration: const InputDecoration(labelText: 'New password (8+ chars)')),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Change')),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    try {
      await context.read<AuthState>().api.changePassword(oldCtrl.text, newCtrl.text);
      if (mounted) showInfo(context, 'Password changed');
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthState>();
    final s = _settings;
    return ListView(
      children: [
        ListTile(
          leading: CircleAvatar(child: Text(auth.user!.username[0].toUpperCase())),
          title: Text(auth.user!.username),
          subtitle: Text(auth.user!.isSuperuser ? 'Superuser' : 'User'),
        ),
        const Divider(),
        if (s == null)
          Padding(
            padding: const EdgeInsets.all(24),
            child: Center(child: _error != null ? Text('$_error') : const CircularProgressIndicator()),
          )
        else ...[
          ListTile(
            leading: const Icon(Icons.directions_car_outlined),
            title: const Text('Travel time after events'),
            subtitle: Text('${s.travelTimeMinutes} min'),
            onTap: _editTravel,
          ),
          ListTile(
            leading: const Icon(Icons.wb_sunny_outlined),
            title: const Text('Day starts'),
            subtitle: Text(s.dayStart),
            onTap: () => _editTime('day_start', s.dayStart),
          ),
          ListTile(
            leading: const Icon(Icons.nightlight_outlined),
            title: const Text('Day ends'),
            subtitle: Text(
              s.dayEnd.compareTo(s.dayStart) <= 0 ? '${s.dayEnd} (next day)' : s.dayEnd,
            ),
            onTap: () => _editTime('day_end', s.dayEnd),
          ),
        ],
        const Divider(),
        ListTile(
          leading: const Icon(Icons.password),
          title: const Text('Change password'),
          onTap: _changePassword,
        ),
        if (auth.user!.isSuperuser)
          ListTile(
            leading: const Icon(Icons.admin_panel_settings_outlined),
            title: const Text('Manage users'),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const AdminScreen()),
            ),
          ),
        ListTile(
          leading: const Icon(Icons.logout),
          title: const Text('Sign out'),
          onTap: auth.logout,
        ),
      ],
    );
  }
}
