import 'dart:async';
import 'package:flutter/material.dart';
import 'package:frontend/pages/home_page.dart';
import 'package:frontend/utils/persistence/global_bloc.dart';
import 'package:provider/provider.dart';
import '../utils/persistence/secure_storage.dart';
import '../utils/persistence/screen_arguments.dart'; // Ensure this is the correct import

class SplashPage extends StatefulWidget {
  static const String routeName =
      '/splash'; // Add a route name if you're using named routes

  @override
  _SplashPageState createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  @override
  void initState() {
    super.initState();
    startTimer();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          image: DecorationImage(
            image:
                AssetImage("images/logo.png"), // Make sure the path is correct
            fit: BoxFit.cover,
          ),
        ),
      ),
    );
  }

  void startTimer() {
    Timer(Duration(seconds: 1),
        navigateUser); // Updated to 2 seconds for better UX
  }

  void navigateUser() async {
    // Initialize SecureStorage
    SecureStorage secureStorage = SecureStorage();
    // Attempt to read the token from secure storage
    String? token = await secureStorage.read('token');
    token = "12334";
    final GlobalBloc globalBloc =
        Provider.of<GlobalBloc>(context, listen: false);

    await globalBloc.onUserLogin(token!);

    if (token != 'No data found!' && token.isNotEmpty) {
      Navigator.pushReplacementNamed(context, HomePage.routeName,
          arguments: ScreenArguments(token));
    } else {
      print("navigating home");
      Navigator.pushReplacementNamed(context, HomePage.routeName);
      print("dis didnt work");
    }
  }
}
