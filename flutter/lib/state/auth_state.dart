import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config.dart';
import '../models/user.dart';
import '../services/api_client.dart';

/// Holds the API client, the JWT and the logged-in user; persists token and server URL.
class AuthState extends ChangeNotifier {
  static const _kToken = 'token';
  static const _kServer = 'server_url';

  final ApiClient api = ApiClient(defaultApiUrl);
  User? user;
  bool loading = true;

  bool get isLoggedIn => user != null;
  String get serverUrl => api.baseUrl;

  AuthState() {
    api.onUnauthorized = logout;
  }

  Future<void> restore() async {
    final prefs = await SharedPreferences.getInstance();
    api.baseUrl = prefs.getString(_kServer) ?? defaultApiUrl;
    api.token = prefs.getString(_kToken);
    if (api.token != null) {
      try {
        user = await api.me();
      } catch (_) {
        api.token = null;
      }
    }
    loading = false;
    notifyListeners();
  }

  Future<void> setServerUrl(String url) async {
    api.baseUrl = url.trim().replaceAll(RegExp(r'/+$'), '');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kServer, api.baseUrl);
    notifyListeners();
  }

  Future<void> login(String username, String password) async {
    api.token = await api.login(username, password);
    user = await api.me();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kToken, api.token!);
    notifyListeners();
  }

  Future<void> register(String username, String password) async {
    await api.register(username, password);
    await login(username, password);
  }

  Future<void> logout() async {
    api.token = null;
    user = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kToken);
    notifyListeners();
  }
}
