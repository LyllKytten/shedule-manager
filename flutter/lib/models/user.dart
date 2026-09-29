class User {
  final int id;
  final String username;
  final bool isActive;
  final bool isSuperuser;

  User({
    required this.id,
    required this.username,
    required this.isActive,
    required this.isSuperuser,
  });

  factory User.fromJson(Map<String, dynamic> j) => User(
        id: j['id'] as int,
        username: j['username'] as String,
        isActive: j['is_active'] as bool,
        isSuperuser: j['is_superuser'] as bool,
      );
}
