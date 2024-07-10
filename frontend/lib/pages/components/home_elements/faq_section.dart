import 'package:flutter/material.dart';
import 'package:frontend/utils/formatting/app_theme.dart';

class FAQSection extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(vertical: 40, horizontal: 400),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Align(
            alignment: Alignment.center,
            child: Text(
              'Get Your Questions Answered',
              style: TextStyle(fontSize: 15, color: primaryColor),
            ),
          ),
          SizedBox(height: 10),
          const Align(
            alignment: Alignment.center,
            child: Text(
              'Frequently Asked Questions',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
          ),
          SizedBox(height: 16),
          FAQItem(
            question: '1. What type of file can I export my clip as?',
            answer:
                'Clips can be exported as PDFs, Word docs, or uploaded directly to Canva.',
          ),
          SizedBox(height: 5),
          Divider(),
          SizedBox(height: 5),
          FAQItem(
            question:
                '2. Which elements of the story will be included in my clip?',
            answer:
                'Clips will include all key elements including the outlet title, article title, byline, introductory paragraph, and relevant sections which include the keyword.',
          ),
          SizedBox(height: 5),
          Divider(),
          SizedBox(height: 5),
          FAQItem(
            question:
                '3. Can I edit my clip if I need to customize or edit it further?',
            answer:
                'Yes, clips can be exported as Word docs or uploaded directly to Canva for further editing and customization.',
          ),
          SizedBox(height: 5),
          Divider(),
          SizedBox(height: 5),
          FAQItem(
            question:
                '4. How can I filter the story for only the relevant sections?',
            answer:
                'Using the keyword search box, you can filter the story to include only the relevant sections to your brand or product.',
          ),
        ],
      ),
    );
  }
}

class FAQItem extends StatelessWidget {
  final String question;
  final String answer;

  FAQItem({required this.question, required this.answer});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            flex: 1,
            child: Text(
              question,
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          SizedBox(width: 16),
          Expanded(
            flex: 1,
            child: Text(answer),
          ),
        ],
      ),
    );
  }
}
