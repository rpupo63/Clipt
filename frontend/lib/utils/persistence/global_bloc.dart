import 'package:flutter/material.dart';
import 'package:frontend/utils/models/user.dart';
import '../BaseAPI.dart';

class GlobalBloc with ChangeNotifier {
  static final GlobalBloc _singleton = GlobalBloc._internal();

  factory GlobalBloc() {
    return _singleton;
  }

  GlobalBloc._internal() {
    currentUser = User.defaultUser();
  }

  late User currentUser;

  Future<void> onUserLogin(String token) async {
    AuthAPI _authAPI = AuthAPI();

    User user = await _authAPI.getUser(token);
    this.currentUser = user;
    notifyListeners();
  }

  Future<void> onUserLogout() async {
    currentUser = User.defaultUser();
    notifyListeners();
  }

  @override
  void dispose() {
    super.dispose();
  }
}
