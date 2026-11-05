import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config.dart';
import '../models/recommend_response.dart';
import 'api_exception.dart';

/// Thin HTTP client. Song selection stays on the Python API.
class ApiClient {
  ApiClient({http.Client? httpClient, String? baseUrl})
      : _http = httpClient ?? http.Client(),
        _baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  final http.Client _http;
  final String _baseUrl;

  Uri _uri(String path) => Uri.parse('$_baseUrl$path');

  Future<Map<String, dynamic>> health() async {
    try {
      final response = await _http.get(_uri('/health')).timeout(
            const Duration(seconds: 5),
          );
      if (response.statusCode != 200) {
        throw ApiException('API health check failed (${response.statusCode}).');
      }
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on ApiException {
      rethrow;
    } catch (_) {
      throw ApiException(
        'Cannot reach the recommendation API at $_baseUrl. '
        'Start FastAPI from the EmoDJ folder, then retry.',
      );
    }
  }

  Future<RecommendResponse> recommend({
    required String emotion,
    required String mode,
    required String category,
    int limit = AppConfig.defaultLimit,
  }) async {
    try {
      final response = await _http
          .post(
            _uri('/recommend'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'emotion': emotion,
              'mode': mode,
              'category': category,
              'limit': limit,
            }),
          )
          .timeout(const Duration(seconds: 10));

      final decoded = jsonDecode(response.body);
      if (response.statusCode != 200) {
        throw ApiException(_detailFrom(decoded, response.statusCode));
      }
      return RecommendResponse.fromJson(decoded as Map<String, dynamic>);
    } on ApiException {
      rethrow;
    } catch (_) {
      throw ApiException(
        'Cannot reach the recommendation API at $_baseUrl.',
      );
    }
  }

  String _detailFrom(dynamic decoded, int statusCode) {
    if (decoded is Map && decoded['detail'] != null) {
      return decoded['detail'].toString();
    }
    return 'Recommendation failed (HTTP $statusCode).';
  }
}
