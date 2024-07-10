import 'package:flutter/material.dart';
import 'package:frontend/pages/components/footer.dart';
import 'package:frontend/pages/components/header.dart';
import 'package:frontend/pages/components/home_elements/faq_section.dart';
import 'package:frontend/pages/components/home_elements/intro_section.dart';
import 'package:frontend/pages/components/home_elements/feature_section.dart';
import 'package:frontend/pages/components/home_elements/pricing_section.dart';
import 'package:frontend/pages/components/home_elements/streamline_section.dart';
import 'package:frontend/utils/buttons/blue_button.dart';

class HomePage extends StatefulWidget {
  final String token;
  static const routeName = '/home';

  const HomePage({Key? key, required this.token}) : super(key: key);

  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  void initState() {
    super.initState();
    print("page_loading");
    //_loadData();
  }
/*
  Future<void> _loadData() async {
    final GlobalBloc globalBloc =
        Provider.of<GlobalBloc>(context, listen: false);
    globalBloc.onUserLogin(widget.token);
  }
*/

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: Header(),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              height: 600,
              child: IntroSection(),
            ),
            SizedBox(
              height: 600,
              child: FeatureSection(),
            ),
            Center(
              child: SizedBox(
                //width: 100, // Set the desired width
                height: 150, // Set the desired height
                child: Container(
                  color: Color(0xFFF5F5FA), // Set the desired color
                ),
              ),
            ),
            SizedBox(
              height: 400,
              child: StreamlineSection(),
            ),
            Center(
              child: SizedBox(
                //width: 100, // Set the desired width
                height: 150, // Set the desired height
                child: Container(
                  color: Color(0xFFF5F5FA), // Set the desired color
                ),
              ),
            ),
            PricingSection(),
            Center(
              child: SizedBox(
                //width: 100, // Set the desired width
                height: 100, // Set the desired height
                child: Container(
                  color: Color(0xFFF5F5FA), // Set the desired color
                ),
              ),
            ),
            FAQSection(),
            Center(
              child: SizedBox(
                //width: 100, // Set the desired width
                height: 100, // Set the desired height
                child: Container(
                  color: Color(0xFFF5F5FA), // Set the desired color
                ),
              ),
            ),
            Center(
              child: SizedBox(
                height: 100, // Set the desired height
                child: Container(
                  color: Color(0xFFF5F5FA), // Set the desired color
                  child: Center(
                      child: BlueButton(
                    text: "Still have questions? Contact us",
                    onPressed: () {
                      print('Button Pressed');
                    },
                  )),
                ),
              ),
            ),
            Footer(),
          ],
        ),
      ),
    );
  }
}
