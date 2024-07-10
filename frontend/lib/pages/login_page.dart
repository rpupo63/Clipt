import 'package:flutter/material.dart';

class LoginPage extends StatelessWidget {
  static const routeName = '/login';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Logo
              Image.asset('images/logo.png',
                  height: 50), // Add your logo asset here
              SizedBox(height: 50),
              // Google Sign-In Button
              ElevatedButton.icon(
                icon: Icon(Icons.login),
                label: Text('Continue with Google'),
                onPressed: () {},
                style: ElevatedButton.styleFrom(
                  minimumSize: Size(double.infinity, 50),
                ),
              ),
              SizedBox(height: 20),
              Text('OR', style: TextStyle(color: Colors.grey)),
              SizedBox(height: 20),
              // Email Input
              TextField(
                decoration: InputDecoration(
                  border: OutlineInputBorder(),
                  labelText: 'Email address',
                  hintText: 'example@gmail.com',
                ),
              ),
              SizedBox(height: 20),
              // Continue with Email Button
              ElevatedButton(
                onPressed: () {},
                child: Text('Continue with email'),
                style: ElevatedButton.styleFrom(
                  minimumSize: Size(double.infinity, 50),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
