import 'package:flutter/material.dart';
import 'package:frontend/utils/buttons/blue_button.dart';
import 'package:frontend/utils/formatting/app_theme.dart';

class PricingSection extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 400),
      child: Column(
        children: [
          const Text(
            'Premium packages',
            style: TextStyle(fontSize: 18, color: primaryColor),
          ),
          SizedBox(height: 10),
          const Text(
            'Choose your package, for any size team.',
            style: TextStyle(fontSize: 25),
          ),
          SizedBox(height: 25),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildPackageCard(
                title: 'Individual',
                price: '\$49.99/mo',
                description: 'For a single user',
                elevation: 0,
                color: Colors.transparent,
              ),
              Stack(
                children: [
                  _buildPackageCard(
                    title: 'Silver',
                    price: '\$99.99/mo',
                    description: 'For teams with up to 5 users',
                    elevation: 10,
                    color: Colors.white,
                  ),
                  Positioned(
                    top: 0,
                    left: 0,
                    right: 0,
                    child: Align(
                      alignment: Alignment.center,
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 70, vertical: 4),
                        decoration: const BoxDecoration(
                          color: Colors.blue,
                          borderRadius: BorderRadius.only(
                            topRight: Radius.circular(8),
                            topLeft: Radius.circular(8),
                          ),
                        ),
                        child: const Text(
                          'HIGHLY RECOMMENDED',
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              _buildPackageCard(
                title: 'Gold',
                price: '\$199.99/mo',
                description: 'For teams with up to 10 users',
                elevation: 0,
                color: Colors.transparent,
              ),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildPackageCard(
      {required String title,
      required String price,
      required String description,
      required double elevation,
      required Color color}) {
    return Card(
      color: color,
      elevation: elevation,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
      ),
      child: Container(
        width: 300,
        height: 450,
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            const SizedBox(height: 20),
            Align(
              alignment: Alignment.bottomLeft,
              child: Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            SizedBox(height: 20),
            Align(
              alignment: Alignment.bottomLeft,
              child: Text(
                description,
                style: TextStyle(fontSize: 16),
              ),
            ),
            SizedBox(height: 50),
            Text(
              price,
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 20),
            BlueButton(
              text: 'Start Free Trial',
              onPressed: () {
                print('Button Pressed');
              },
            ),
            SizedBox(height: 30),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildFeature('Unlimited clips per month'),
                SizedBox(height: 25),
                _buildFeature('No contract, cancel at any time'),
                SizedBox(height: 25),
                _buildFeature('24/7 support'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeature(String feature) {
    return Row(
      children: [
        Icon(Icons.check, color: Colors.green),
        SizedBox(width: 8),
        Text(feature),
      ],
    );
  }
}
