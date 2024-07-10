import 'package:flutter/material.dart';
import 'package:frontend/utils/formatting/app_theme.dart';

class BlueButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;

  const BlueButton({super.key, required this.text, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        backgroundColor: primaryButtonColor,
        foregroundColor: Colors.white,
        padding: EdgeInsets.symmetric(horizontal: 30, vertical: 15),
        textStyle: const TextStyle(
            fontSize: 16, color: Colors.white, fontFamily: displayFont),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(
              8), // Adjust the value to make corners less rounded
        ),
      ),
      onPressed: onPressed,
      child: Text(text),
    );
  }
}
