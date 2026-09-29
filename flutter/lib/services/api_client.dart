import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/event.dart';
import '../models/user.dart';
import '../models/user_settings.dart';
import '../utils/format.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);

  @override
  String toString() => message;
}

/// Thin wrapper around the Schedule Manager REST API (see backend/).
class ApiClient {
  String baseUrl;
  String? token;

  /// Called on 401 so the app can drop the session and show the login screen.
  void Function()? onUnauthorized;

  ApiClient(this.baseUrl, {this.token});

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  Uri _uri(String path, [Map<String, String>? query]) =>
      Uri.parse('$baseUrl$path').replace(queryParameters: query);

  dynamic _decode(http.Response r) {
    if (r.statusCode == 401 && token != null) onUnauthorized?.call();
    final body = r.body.isEmpty ? null : jsonDecode(utf8.decode(r.bodyBytes));
    if (r.statusCode >= 400) {
      var msg = 'Error ${r.statusCode}';
      if (body is Map && body['detail'] != null) {
        final d = body['detail'];
        msg = d is String ? d : (d is List && d.isNotEmpty ? d.first['msg'].toString() : d.toString());
      }
      throw ApiException(r.statusCode, msg);
    }
    return body;
  }

  Future<dynamic> _get(String path, [Map<String, String>? q]) async =>
      _decode(await http.get(_uri(path, q), headers: _headers));

  Future<dynamic> _post(String path, Object? body) async =>
      _decode(await http.post(_uri(path), headers: _headers, body: jsonEncode(body)));

  Future<dynamic> _patch(String path, Object? body) async =>
      _decode(await http.patch(_uri(path), headers: _headers, body: jsonEncode(body)));

  Future<dynamic> _delete(String path) async =>
      _decode(await http.delete(_uri(path), headers: _headers));

  // ---------- auth ----------

  Future<String> login(String username, String password) async {
    final r = await http.post(
      _uri('/auth/login'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {'username': username, 'password': password},
    );
    return _decode(r)['access_token'] as String;
  }

  Future<void> register(String username, String password) =>
      _post('/auth/register', {'username': username, 'password': password});

  Future<User> me() async => User.fromJson(await _get('/auth/me'));

  Future<void> changePassword(String oldPassword, String newPassword) => _post(
        '/auth/change-password',
        {'old_password': oldPassword, 'new_password': newPassword},
      );

  // ---------- events ----------

  Future<List<Event>> events(DateTime start, [DateTime? end]) async {
    final list = await _get('/events', {
      'start': apiDate(start),
      if (end != null) 'end': apiDate(end),
    }) as List;
    return list.map((e) => Event.fromJson(e)).toList();
  }

  Future<List<FreeSlot>> freeSlots(DateTime day) async {
    final r = await _get('/events/free', {'day': apiDate(day)});
    return (r['slots'] as List).map((e) => FreeSlot.fromJson(e)).toList();
  }

  /// Free slots for 7 days starting at [start], one entry per day.
  Future<List<DayFreeSlots>> freeWeek(DateTime start) async {
    final list = await _get('/events/free/week', {'start': apiDate(start)}) as List;
    return list.map((e) => DayFreeSlots.fromJson(e)).toList();
  }

  Future<void> createEvent(NewEvent e) => _post('/events', e.toJson());

  Future<void> updateEvent(int id, Map<String, dynamic> fields) =>
      _patch('/events/$id', fields);

  Future<void> deleteEvent(int id) => _delete('/events/$id');

  Future<void> deleteSeries(String seriesId) => _delete('/events/series/$seriesId');

  // ---------- settings ----------

  Future<UserSettings> settings() async => UserSettings.fromJson(await _get('/settings'));

  Future<UserSettings> updateSettings(Map<String, dynamic> fields) async =>
      UserSettings.fromJson(await _patch('/settings', fields));

  // ---------- admin ----------

  Future<List<User>> adminUsers() async =>
      ((await _get('/admin/users')) as List).map((e) => User.fromJson(e)).toList();

  Future<void> adminCreateUser(String username, String password, bool isSuperuser) =>
      _post('/admin/users', {
        'username': username,
        'password': password,
        'is_superuser': isSuperuser,
      });

  Future<void> adminUpdateUser(int id, Map<String, dynamic> fields) =>
      _patch('/admin/users/$id', fields);

  Future<void> adminDeleteUser(int id) => _delete('/admin/users/$id');
}
