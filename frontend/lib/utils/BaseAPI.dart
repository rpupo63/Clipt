import 'dart:convert';
import 'package:frontend/utils/models/user.dart';
import 'package:http/http.dart' as http;

class BaseAPI {
  static String api =
      "http://localhost:8080"; //"https://pronexus-production.up.railway.app"
  Uri userPath = Uri.parse('$api/me');
  Uri loginPath = Uri.parse('$api/login');
  Uri logoutPath = Uri.parse("$api/logout");
  Uri signupPath = Uri.parse("$api/signup");

  Map<String, String> headers = {
    "Content-Type": "application/json; charset=UTF-8"
  };
}

class AuthAPI extends BaseAPI {
  Future<http.Response> signup(User user) async {
    var body = jsonEncode({
      'fullName': user.fullName,
      'email': user.email,
      'password': user.password,
      'organizationID': user.organizationId,
      'admin': user.admin,
    });
    http.Response response =
        await http.post(super.signupPath, headers: super.headers, body: body);
    return response;
  }

  Future<http.Response> login(String email, String password) async {
    var headers = {
      'Content-Type': 'application/json',
      // Add any other necessary headers here, like authorization tokens
    };
    var body = jsonEncode({'email': email, 'password': password});

    http.Response response =
        await http.post(super.loginPath, headers: headers, body: body);

    return response;
  }

  Future<User> getUser(String token) async {
    try {
      final response = await http
          .get(userPath, headers: {"Authorization": "Bearer ${token}"});
      if (response.statusCode == 200) {
        User user = User.fromJson(json.decode(response.body));
        return user;
      } else {
        return User.defaultUser();
      }
    } catch (e) {
      return User.defaultUser();
    }
  }

  Future<http.Response> logout(String token) async {
    final response = await http.post(
      logoutPath,
      headers: {
        'Authorization': token,
      },
    );
    return response;
  }
}
