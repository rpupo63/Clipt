import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorage {
  final FlutterSecureStorage storage = const FlutterSecureStorage();

  Future write(String k, String v) async {
    await storage.write(key: k, value: v);
  }

  read(String k) async {
    String value = await storage.read(key: k) ?? 'No data found!';
    return value;
  }

  delete(String k) async {
    await storage.delete(key: k);
  }
}
