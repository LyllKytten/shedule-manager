import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/user.dart';
import '../state/auth_state.dart';
import '../widgets/common.dart';

/// Superuser-only: list, create, (de)activate, promote and delete accounts.
class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key});

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  late Future<List<User>> _users;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    final api = context.read<AuthState>().api;
    setState(() {
      _users = api.adminUsers();
    });
  }

  Future<void> _run(Future<void> Function() action) async {
    try {
      await action();
      _load();
    } catch (e) {
      if (mounted) showError(context, e);
    }
  }

  Future<void> _create() async {
    final name = TextEditingController();
    final pass = TextEditingController();
    var superuser = false;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setLocal) => AlertDialog(
          title: const Text('New user'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: name, decoration: const InputDecoration(labelText: 'Username')),
              TextField(controller: pass, obscureText: true, decoration: const InputDecoration(labelText: 'Password (8+ chars)')),
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Superuser'),
                value: superuser,
                onChanged: (v) => setLocal(() => superuser = v ?? false),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Create')),
          ],
        ),
      ),
    );
    if (ok == true && mounted) {
      final api = context.read<AuthState>().api;
      _run(() => api.adminCreateUser(name.text.trim(), pass.text, superuser));
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthState>();
    final api = auth.api;
    return Scaffold(
      appBar: AppBar(title: const Text('Users')),
      floatingActionButton: FloatingActionButton(onPressed: _create, child: const Icon(Icons.person_add)),
      body: FutureBuilder(
        future: _users,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) return Center(child: Text('${snap.error}'));
          return ListView(
            children: snap.data!.map((u) {
              final self = u.id == auth.user!.id;
              return ListTile(
                leading: Icon(u.isSuperuser ? Icons.shield : Icons.person,
                    color: u.isActive ? null : Theme.of(context).colorScheme.outline),
                title: Text(u.username + (self ? ' (you)' : '')),
                subtitle: Text([
                  if (u.isSuperuser) 'superuser',
                  u.isActive ? 'active' : 'disabled',
                ].join(' · ')),
                trailing: self
                    ? null
                    : PopupMenuButton<String>(
                        onSelected: (a) => switch (a) {
                          'toggle_active' => _run(() => api.adminUpdateUser(u.id, {'is_active': !u.isActive})),
                          'toggle_super' => _run(() => api.adminUpdateUser(u.id, {'is_superuser': !u.isSuperuser})),
                          _ => _run(() => api.adminDeleteUser(u.id)),
                        },
                        itemBuilder: (_) => [
                          PopupMenuItem(value: 'toggle_active', child: Text(u.isActive ? 'Disable' : 'Enable')),
                          PopupMenuItem(value: 'toggle_super', child: Text(u.isSuperuser ? 'Remove superuser' : 'Make superuser')),
                          const PopupMenuItem(value: 'delete', child: Text('Delete')),
                        ],
                      ),
              );
            }).toList(),
          );
        },
      ),
    );
  }
}
