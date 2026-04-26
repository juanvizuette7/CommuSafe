import 'package:dio/dio.dart';

import '../constants/app_constants.dart';
import 'storage_service.dart';

class ApiService {
  ApiService._();

  static final Dio _dio = Dio();
  static final Dio _refreshDio = Dio();
  static bool _initialized = false;

  static Future<void> init() async {
    if (_initialized) {
      return;
    }

    final baseOptions = BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: AppConstants.requestTimeout,
      receiveTimeout: AppConstants.requestTimeout,
      sendTimeout: AppConstants.requestTimeout,
      headers: <String, dynamic>{
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    );

    _dio.options = baseOptions;
    _refreshDio.options = baseOptions;

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest:
            (RequestOptions options, RequestInterceptorHandler handler) async {
              final token = await StorageService.getAccessToken();
              if (token != null &&
                  token.isNotEmpty &&
                  options.extra['omitAuth'] != true) {
                options.headers['Authorization'] = 'Bearer $token';
              }
              handler.next(options);
            },
        onError: (DioException error, ErrorInterceptorHandler handler) async {
          final statusCode = error.response?.statusCode;
          final alreadyRetried = error.requestOptions.extra['retried'] == true;
          final isRefreshRequest =
              error.requestOptions.path == AppConstants.refreshEndpoint;

          if (statusCode == 401 && !alreadyRetried && !isRefreshRequest) {
            final refreshed = await _refreshToken();
            if (refreshed) {
              try {
                final retryResponse = await _retryRequest(error.requestOptions);
                return handler.resolve(retryResponse);
              } on DioException catch (retryError) {
                return handler.next(retryError);
              }
            }

            await StorageService.clearSession();
          }

          handler.next(error);
        },
      ),
    );

    _initialized = true;
  }

  static Future<bool> _refreshToken() async {
    final refreshToken = await StorageService.getRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      return false;
    }

    try {
      final response = await _refreshDio.post<Map<String, dynamic>>(
        AppConstants.refreshEndpoint,
        data: <String, dynamic>{'refresh': refreshToken},
        options: Options(extra: <String, dynamic>{'omitAuth': true}),
      );

      final responseData = response.data ?? <String, dynamic>{};
      final newAccessToken = responseData['access'] as String?;
      final newRefreshToken =
          responseData['refresh'] as String? ?? refreshToken;

      if (newAccessToken == null || newAccessToken.isEmpty) {
        return false;
      }

      await StorageService.saveTokens(
        accessToken: newAccessToken,
        refreshToken: newRefreshToken,
      );

      return true;
    } on DioException {
      return false;
    }
  }

  static Future<Response<dynamic>> _retryRequest(
    RequestOptions requestOptions,
  ) async {
    final freshToken = await StorageService.getAccessToken();
    final headers = Map<String, dynamic>.from(requestOptions.headers);
    if (freshToken != null && freshToken.isNotEmpty) {
      headers['Authorization'] = 'Bearer $freshToken';
    }

    final options = Options(
      method: requestOptions.method,
      headers: headers,
      responseType: requestOptions.responseType,
      contentType: requestOptions.contentType,
      followRedirects: requestOptions.followRedirects,
      receiveDataWhenStatusError: requestOptions.receiveDataWhenStatusError,
      validateStatus: requestOptions.validateStatus,
      extra: <String, dynamic>{...requestOptions.extra, 'retried': true},
    );

    return _dio.request<dynamic>(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
      cancelToken: requestOptions.cancelToken,
      onReceiveProgress: requestOptions.onReceiveProgress,
      onSendProgress: requestOptions.onSendProgress,
    );
  }

  static Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    await init();
    return _dio.get<T>(
      path,
      queryParameters: queryParameters,
      options: options,
    );
  }

  static Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    await init();
    return _dio.post<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  static Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    await init();
    return _dio.put<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  static Future<Response<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    await init();
    return _dio.patch<T>(
      path,
      data: data,
      queryParameters: queryParameters,
      options: options,
    );
  }

  static Future<Response<T>> postMultipart<T>(
    String path, {
    Map<String, dynamic>? data,
    List<MultipartFile>? files,
    String fileFieldName = 'imagenes',
    Map<String, dynamic>? queryParameters,
  }) async {
    await init();

    final formData = FormData.fromMap(data ?? <String, dynamic>{});
    for (final file in files ?? <MultipartFile>[]) {
      formData.files.add(MapEntry<String, MultipartFile>(fileFieldName, file));
    }

    return _dio.post<T>(
      path,
      data: formData,
      queryParameters: queryParameters,
      options: Options(contentType: 'multipart/form-data'),
    );
  }
}
