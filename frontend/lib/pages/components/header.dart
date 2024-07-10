import 'package:flutter/material.dart';
import 'package:frontend/utils/buttons/blue_button.dart';

class Header extends StatelessWidget implements PreferredSizeWidget {
  const Header({super.key});

  @override
  Widget build(BuildContext context) {
    return AppBar(
      backgroundColor: const Color(0xFFFFFFFF),
      elevation: 0,
      title: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              InkWell(
                onTap: () {
                  // Define the action to be taken when the image is clicked
                  print('Image clicked');
                  // You can navigate to a new page, show a dialog, etc.
                },
                child: Image.asset(
                  'images/logo.png', // Add your logo here
                  height: 40,
                ),
              ),
              SizedBox(width: 20),
              TextButton(
                onPressed: () {},
                child: Text('Features', style: TextStyle(color: Colors.black)),
              ),
              TextButton(
                onPressed: () {},
                child: Text('Pricing', style: TextStyle(color: Colors.black)),
              ),
              TextButton(
                onPressed: () {},
                child: Text('Resources', style: TextStyle(color: Colors.black)),
              ),
              TextButton(
                onPressed: () {},
                child:
                    Text('Contact Us', style: TextStyle(color: Colors.black)),
              ),
            ],
          ),
          Row(
            children: [
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.transparent, // Background color
                    padding: EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                    elevation: 0),
                onPressed: () {
                  print("Login Pressed");
                },
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.lock, color: Colors.black),
                    SizedBox(width: 8), // Adjust space between icon and text
                    Text(
                      'Login',
                      style: TextStyle(color: Colors.black),
                    ),
                  ],
                ),
              ),
              SizedBox(width: 10),
              BlueButton(
                text: 'Get Started for FREE',
                onPressed: () {
                  // Define the action when the button is pressed
                  print('Button Pressed');
                },
              ),
            ],
          ),
        ],
      ),
    );
  }

  @override
  Size get preferredSize => Size.fromHeight(kToolbarHeight);
}
