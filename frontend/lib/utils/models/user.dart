class User {
  String? userId;
  String email;
  String fullName;
  String password;
  String organizationId;
  String? projectId; // Updated to be non-nullable
  DateTime? dateOnboarded;
  List<String>? pastProjectIDs;
  bool admin;
  DateTime? signedAt; // Added field to match Go model
  String? token; // Added field to match Go model

  User({
    this.userId,
    required this.email,
    required this.fullName,
    required this.password,
    required this.organizationId,
    this.projectId, // Ensure it's initialized as required
    this.dateOnboarded,
    this.pastProjectIDs,
    required this.admin,
    this.signedAt,
    this.token,
  });

  // Default constructor with sensible defaults
  User.defaultUser()
      : userId = '',
        email = '',
        fullName = '',
        password = '',
        organizationId = '',
        projectId = '',
        admin = false;

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      userId: json['id'] as String?,
      email: json['email'] as String,
      fullName: json['fullName'] as String,
      password: json['password'] as String,
      organizationId: json['organizationId'] as String,
      projectId: json['projectId'] as String,
      dateOnboarded: json['dateOnboarded'] == null
          ? null
          : DateTime.parse(json['dateOnboarded']),
      pastProjectIDs: (json['pastProjectIDs'] as List<dynamic>?)
          ?.map((item) => item as String)
          .toList(),
      admin: json['admin'] as bool,
      signedAt:
          json['signedAt'] == null ? null : DateTime.parse(json['signedAt']),
      token: json['token'] as String?,
    );
  }
}
