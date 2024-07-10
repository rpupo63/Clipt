//import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:frontend/pages/home_page.dart';
import 'package:frontend/pages/login_page.dart';
import 'package:frontend/pages/splash_page.dart';
import 'package:frontend/utils/formatting/app_theme.dart';
import 'package:frontend/utils/persistence/global_bloc.dart';
import 'package:provider/provider.dart';
import 'utils/persistence/screen_arguments.dart';

Future<void> main() async {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (context) => GlobalBloc(),
        ),
        // Add other providers if necessary
      ],
      child: const Clipt(),
    ),
  );
}

class Clipt extends StatefulWidget {
  const Clipt({super.key});

  @override
  _CliptState createState() => _CliptState();
}

class _CliptState extends State<Clipt> {
  final Map<String, Widget Function(ScreenArguments)> routeBuilders = {
    HomePage.routeName: (args) => HomePage(token: args.token),
  };

  Key key = UniqueKey();

  void resetGlobalBloc() {
    setState(() {
      key = UniqueKey(); // Changing the key rebuilds the widget
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      //key: key,
      title: 'ProNexus',
      routes: {
        '/login': (context) => LoginPage(),
        '/': (context) => SplashPage(),
        '/splash': (context) => SplashPage()
      },
      onGenerateRoute: (settings) {
        if (routeBuilders.containsKey(settings.name)) {
          final args = settings.arguments as ScreenArguments;
          return MaterialPageRoute(
            builder: (context) => routeBuilders[settings.name]!(args),
          );
        }
        assert(false, 'Need to implement ${settings.name}');
        return null;
      },
      theme: lightTheme,
    );
  }
}
