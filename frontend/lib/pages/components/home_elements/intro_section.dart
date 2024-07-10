import 'package:flutter/material.dart';
import 'package:frontend/utils/buttons/blue_button.dart';
import 'package:frontend/utils/formatting/app_theme.dart';

class IntroSection extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      color: Color(0xFFF5F5FA),
      padding: EdgeInsets.symmetric(vertical: 40, horizontal: 100),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Left side
          Expanded(
            flex: 1,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Clipt does the clipping for you',
                  style: TextStyle(
                      fontSize: 60,
                      fontWeight: FontWeight.bold,
                      color: secondaryColor),
                ),
                const Text(
                  'so you can focus on what matters.',
                  style: TextStyle(
                      fontSize: 60,
                      fontWeight: FontWeight.bold,
                      color: primaryColor),
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    const Expanded(
                      child: TextField(
                        decoration: InputDecoration(
                          hintText: 'Type your email',
                          hintStyle: TextStyle(
                            color: Colors.grey,
                          ),
                          filled: true,
                          fillColor: Colors.white,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.all(
                              Radius.circular(5.0),
                            ),
                            borderSide: BorderSide.none,
                          ),
                        ),
                      ),
                    ),
                    SizedBox(width: 10),
                    BlueButton(
                      text: 'Get Started for FREE',
                      onPressed: () {
                        // Define the action when the button is pressed
                        print('Button Pressed');
                      },
                    )
                  ],
                ),
              ],
            ),
          ),
          // Right side
          Expanded(
            flex: 1,
            child: Center(
              child: Image.asset(
                'assets/image.png', // Replace with the path to your image
                fit: BoxFit.contain,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
