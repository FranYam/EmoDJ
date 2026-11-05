import 'package:flutter/material.dart';

import 'screens/home_screen.dart';
import 'services/api_client.dart';
import 'theme.dart';

void main() {
  runApp(EmoDjApp(api: ApiClient()));
}

class EmoDjApp extends StatelessWidget {
  const EmoDjApp({super.key, required this.api});

  final ApiClient api;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EmoDJ',
      debugShowCheckedModeBanner: false,
      theme: buildEmoDjTheme(),
      home: HomeScreen(api: api),
    );
  }
}
