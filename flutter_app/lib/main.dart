import 'package:flutter/material.dart';

import 'screens/home_screen.dart';
import 'theme.dart';

void main() {
  runApp(const GeoidApp());
}

class GeoidApp extends StatelessWidget {
  const GeoidApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GeoiD-vpn',
      debugShowCheckedModeBanner: false,
      theme: temaGeoid(),
      home: const HomeScreen(),
    );
  }
}
