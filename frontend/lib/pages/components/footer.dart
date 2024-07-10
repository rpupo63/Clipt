import 'package:flutter/material.dart';
import 'package:frontend/utils/buttons/blue_button.dart';

class Footer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      color: Color(0xFF00113B), // Background color
      width: double.infinity,
      height: 350, // Adjust the height as needed
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          SizedBox(height: 40),
          const Text(
            'Get clipping.',
            style: TextStyle(
              color: Colors.white,
              fontSize: 64,
            ),
          ),
          SizedBox(height: 20),
          BlueButton(
              text: "Get Started for FREE",
              onPressed: () {
                print("pressed");
              }),
          Align(
            alignment: Alignment.bottomLeft,
            child: Padding(
              padding: const EdgeInsets.all(16.0), // Add padding if needed
              child: Image.asset(
                'images/logo.png', // Update this path to your logo asset path
                width: 80, // Adjust the width as needed
                height: 80, // Adjust the height as needed
              ),
            ),
          ),
        ],
      ),
    );
  }
}
