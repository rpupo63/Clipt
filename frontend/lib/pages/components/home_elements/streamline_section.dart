import 'package:flutter/material.dart';
import 'package:frontend/utils/formatting/app_theme.dart';

class StreamlineSection extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      color: secondaryColor,
      padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 200),
      child: const Column(
        mainAxisAlignment: MainAxisAlignment.start, // Align items to the top
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Align(
            alignment: Alignment.centerLeft,
            child: Text(
              'Streamline your workflow with Clipt —',
              style: TextStyle(
                  fontSize: 35,
                  fontWeight: FontWeight.bold,
                  color: Colors.white),
            ),
          ),
          SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.start,
            crossAxisAlignment:
                CrossAxisAlignment.start, // Align children to the top
            children: [
              Flexible(
                child: FeatureItem(
                  Icons.device_hub,
                  'Simple, easy-to-use platform: simply input the article URL and keyword. (keyword search capability)',
                ),
              ),
              Flexible(
                child: FeatureItem(
                  Icons.picture_as_pdf,
                  'Export as a PDF or choose an editable file type for easy customization: Clipt is compatible with Microsoft Word, Google Docs, and Canva.',
                ),
              ),
              Flexible(
                child: FeatureItem(
                  Icons.settings,
                  'PR software solutions are expensive, Clipt offers a one-off clipping automation service at an affordable rate, so you never pay for services you don’t need.',
                ),
              ),
              Flexible(
                child: FeatureItem(
                  Icons.cloud,
                  'The platform can be accessed via the Clipt webpage, no application install required.',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class FeatureItem extends StatelessWidget {
  final IconData icon;
  final String title;

  const FeatureItem(this.icon, this.title);

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(minHeight: 200), // Ensure minimum height
      decoration: BoxDecoration(
        color: Colors.transparent, // Transparent background
        borderRadius: BorderRadius.circular(10), // Rounded corners
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: const BoxDecoration(
              color: primaryColor, // Circle background color
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: Colors.white, size: 40),
          ),
          const SizedBox(height: 10),
          Text(
            title,
            style: const TextStyle(fontSize: 15, color: Colors.white),
            textAlign: TextAlign.left,
          ),
        ],
      ),
    );
  }
}
