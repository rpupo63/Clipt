import 'dart:ui';

import 'package:flex_color_scheme/flex_color_scheme.dart';
import 'package:flutter/material.dart';

const Color primaryColor = Color(0xFF4165FF);
const Color primaryButtonColor = Color(0xFF4165FF);
const Color primaryColorLight = Color(0xff94B2DB);
const Color secondaryColor = Color(0xFF051544);
const Color secondaryColorLight = Color(0xffF6B4BA);
const Color tertiaryColor = Color(0xFF6CA450);

const FlexSubThemesData subThemeData = FlexSubThemesData(
  fabSchemeColor: SchemeColor.secondary,
  inputDecoratorBorderType: FlexInputBorderType.underline,
  inputDecoratorIsFilled: false,
  useTextTheme: true,
  appBarScrolledUnderElevation: 4,
  navigationBarIndicatorOpacity: 0.24,
  navigationBarHeight: 56,
);

const String displayFont = 'Poppins';

const List<FontVariation> displayFontBoldWeight = <FontVariation>[
  FontVariation('wght', 600)
];
const List<FontVariation> displayFontHeavyWeight = <FontVariation>[
  FontVariation('wght', 800)
];

// Make a light ColorScheme from the seeds.
final ColorScheme schemeLight = SeedColorScheme.fromSeeds(
  primary: primaryColor,
  primaryKey: primaryColor,
  secondaryKey: secondaryColor,
  secondary: secondaryColor,
  tertiaryKey: tertiaryColor,
  brightness: Brightness.light,
  tones: FlexTones.vivid(Brightness.light),
);

// Make a dark ColorScheme from the seeds.
final ColorScheme schemeDark = SeedColorScheme.fromSeeds(
  // primary: primaryColor,
  primaryKey: primaryColor,
  secondaryKey: secondaryColor,
  secondary: secondaryColor,
  brightness: Brightness.dark,
  tones: FlexTones.vivid(Brightness.dark),
);

// Make a high contrast light ColorScheme from the seeds
final ColorScheme schemeLightHc = SeedColorScheme.fromSeeds(
  primaryKey: primaryColor,
  secondaryKey: secondaryColor,
  brightness: Brightness.light,
  tones: FlexTones.ultraContrast(Brightness.light),
);

// Make a ultra contrast dark ColorScheme from the seeds.
final ColorScheme schemeDarkHc = SeedColorScheme.fromSeeds(
  primaryKey: primaryColor,
  secondaryKey: secondaryColor,
  brightness: Brightness.dark,
  tones: FlexTones.ultraContrast(Brightness.dark),
);

const textTheme = TextTheme(
  displayLarge: TextStyle(
    fontFamily: displayFont,
    fontVariations: displayFontHeavyWeight,
  ),
  displayMedium: TextStyle(
    fontFamily: displayFont,
    fontVariations: displayFontHeavyWeight,
  ),
  displaySmall: TextStyle(
    fontFamily: displayFont,
    fontVariations: displayFontHeavyWeight,
  ),
  headlineLarge: TextStyle(
    fontFamily: displayFont,
    fontVariations: displayFontBoldWeight,
  ),
  headlineMedium: TextStyle(
    fontFamily: displayFont,
    fontVariations: displayFontBoldWeight,
  ),
  headlineSmall: TextStyle(
    fontFamily: displayFont,
    fontVariations: displayFontBoldWeight,
  ),
  titleLarge: TextStyle(
    fontFamily: displayFont,
    fontVariations: displayFontBoldWeight,
  ),
  titleMedium: TextStyle(
    fontFamily: displayFont,
    fontVariations: displayFontBoldWeight,
  ),
  titleSmall: TextStyle(
    fontFamily: displayFont,
    fontVariations: displayFontBoldWeight,
  ),
);

final lightTheme = FlexThemeData.light(
  colorScheme: schemeLight,
  useMaterial3: true,
  appBarStyle: FlexAppBarStyle.primary,
  subThemesData: subThemeData,
  textTheme: textTheme,
);

final darkTheme = FlexThemeData.dark(
  colorScheme: schemeDark,
  useMaterial3: true,
  subThemesData: subThemeData,
  textTheme: textTheme,
);

final lightThemeHc = FlexThemeData.light(
  colorScheme: schemeLightHc,
  useMaterial3: true,
  appBarStyle: FlexAppBarStyle.primary,
  subThemesData: subThemeData,
  textTheme: textTheme,
);

final darkThemeHc = FlexThemeData.dark(
  colorScheme: schemeDarkHc,
  useMaterial3: true,
  subThemesData: subThemeData,
  textTheme: textTheme,
);
