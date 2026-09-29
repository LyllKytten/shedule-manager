import 'package:flutter/material.dart';

import 'day_view.dart';
import 'event_form_screen.dart';
import 'settings_screen.dart';
import 'week_view.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _tab = 0;
  // Bumped after adding an event so the visible tab reloads.
  int _refresh = 0;

  Future<void> _add() async {
    final added = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => const EventFormScreen()),
    );
    if (added == true) setState(() => _refresh++);
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      DayView(key: ValueKey('day$_refresh')),
      WeekView(key: ValueKey('week$_refresh')),
      const SettingsScreen(),
    ];
    return Scaffold(
      appBar: AppBar(title: Text(const ['Schedule', 'Week', 'Settings'][_tab])),
      body: pages[_tab],
      floatingActionButton: _tab == 2
          ? null
          : FloatingActionButton.extended(
              onPressed: _add,
              icon: const Icon(Icons.add),
              label: const Text('Event'),
            ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.today_outlined), selectedIcon: Icon(Icons.today), label: 'Day'),
          NavigationDestination(icon: Icon(Icons.view_week_outlined), selectedIcon: Icon(Icons.view_week), label: 'Week'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }
}
