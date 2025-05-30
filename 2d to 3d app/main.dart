import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:io';
import 'package:image_picker/image_picker.dart';
import 'dart:convert';
import 'package:path/path.dart' as path;
import 'package:webview_flutter/webview_flutter.dart';
import 'package:url_launcher/url_launcher.dart';

void main() {
  // Add this to allow self-signed certificates if needed
  HttpOverrides.global = MyHttpOverrides();
  runApp(const MyApp());
}

// Custom HTTP overrides to handle self-signed certificates
class MyHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      ..badCertificateCallback =
          (X509Certificate cert, String host, int port) => true;
  }
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TripoSR Demo',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.blue,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blue,
          primary: Colors.blue,
          secondary: Colors.deepPurple,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.blue,
          foregroundColor: Colors.white,
          elevation: 2,
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.blue,
            foregroundColor: Colors.white,
            elevation: 3,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
        cardTheme: CardTheme(
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      home: const MyHomePage(title: '3D Model Generator'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  File? _image;
  bool _isProcessing = false;
  String _resultText = '';
  List<String> _outputFiles = [];
  bool _hasProcessedImage = false;

  // Update these with your actual server domain/IP
  final String serverHost = '192.168.225.144:5000'.trim();

  // Construct URLs without spaces
  String get serverUrl => 'https://$serverHost/process_image';
  String get viewerUrl => 'https://$serverHost/Tviewer';

  Future<void> _getImage(ImageSource source) async {
    final ImagePicker picker = ImagePicker();
    final XFile? pickedFile = await picker.pickImage(
      source: source,
      imageQuality: 90,
    );

    if (pickedFile != null) {
      setState(() {
        _image = File(pickedFile.path);
        _resultText = '';
        _outputFiles = [];
        _hasProcessedImage = false;
      });
    }
  }

  Future<void> _processImage() async {
    if (_image == null) {
      setState(() {
        _resultText = 'Please select an image first';
      });
      return;
    }

    setState(() {
      _isProcessing = true;
      _resultText = 'Processing...';
    });

    // Create multipart request
    final request = http.MultipartRequest('POST', Uri.parse(serverUrl));

    // Add file to request
    request.files.add(await http.MultipartFile.fromPath('image', _image!.path));

    try {
      final response = await request.send();
      final responseBody = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        final jsonResponse = json.decode(responseBody);

        setState(() {
          _resultText = 'Processing complete!';

          if (jsonResponse['output_files'] != null) {
            _outputFiles = List<String>.from(jsonResponse['output_files']);
            _resultText += '\nOutput files: ${_outputFiles.length}';
            _hasProcessedImage = true;
          }

          if (jsonResponse['message'] != null &&
              jsonResponse['message'].toString().isNotEmpty) {
            _resultText += '\n\nOutput message: ${jsonResponse['message']}';
          }

          _isProcessing = false;
        });
      } else {
        setState(() {
          _resultText = 'Error: $responseBody';
          _isProcessing = false;
        });
      }
    } catch (e) {
      setState(() {
        _resultText = 'Connection error: $e';
        _isProcessing = false;
      });
    }
  }

  Future<bool> _checkServerConnectivity() async {
    try {
      print("Checking connectivity to: $viewerUrl");
      final response = await http
          .head(Uri.parse(viewerUrl))
          .timeout(
            const Duration(seconds: 5),
            onTimeout: () {
              print("Connection timeout");
              return http.Response('Timeout', 408);
            },
          );
      print("Server response code: ${response.statusCode}");
      return response.statusCode < 400;
    } catch (e) {
      print("Connectivity error details: $e");
      return false;
    }
  }

  // Method to open external browser for 3D viewer in full screen
  Future<void> _openExternalBrowser() async {
    final Uri url = Uri.parse('https://$serverHost/Tviewer');
    print('Attempting to launch URL: $url');

    try {
      if (!await launchUrl(url, mode: LaunchMode.externalApplication)) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Could not launch $url'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      print('Error launching URL: $e');
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
      );

      // If that fails, show a dialog offering an internal WebView option
      showDialog(
        context: context,
        builder:
            (context) => AlertDialog(
              title: const Text('External Browser Failed'),
              content: const Text(
                'Would you like to try viewing in an in-app browser instead? '
                'This might handle SSL certificate issues better.',
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
                TextButton(
                  onPressed: () {
                    Navigator.pop(context);
                    // Navigate to a WebView implementation
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => WebViewScreen(url: viewerUrl),
                      ),
                    );
                  },
                  child: const Text('Try In-App Browser'),
                ),
              ],
            ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.title,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
        elevation: 4,
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Colors.blue.shade50, Colors.white],
          ),
        ),
        child: Stack(
          children: [
            // Main content
            SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: <Widget>[
                    // Image preview area with styled container
                    Container(
                      width: double.infinity,
                      height: 400, // Increased height
                      decoration: BoxDecoration(
                        color: Colors.grey.shade200,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: Colors.grey.shade300),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.1),
                            blurRadius: 10,
                            offset: const Offset(0, 5),
                          ),
                        ],
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(15),
                        child:
                            _image == null
                                ? Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: const [
                                    Icon(
                                      Icons.image_outlined,
                                      size: 80,
                                      color: Colors.grey,
                                    ),
                                    SizedBox(height: 16),
                                    Text(
                                      'No image selected',
                                      style: TextStyle(
                                        fontSize: 18,
                                        color: Colors.grey,
                                      ),
                                    ),
                                  ],
                                )
                                : Image.file(
                                  _image!,
                                  fit: BoxFit.contain,
                                  width: double.infinity,
                                  height: double.infinity,
                                ),
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Image selection and processing buttons
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: [
                          ElevatedButton.icon(
                            onPressed:
                                _isProcessing
                                    ? null
                                    : () => _getImage(ImageSource.gallery),
                            icon: const Icon(Icons.photo_library),
                            label: const Text('Gallery'),
                            style: ElevatedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 12,
                              ),
                            ),
                          ),
                          ElevatedButton.icon(
                            onPressed:
                                _isProcessing
                                    ? null
                                    : () => _getImage(ImageSource.camera),
                            icon: const Icon(Icons.camera_alt),
                            label: const Text('Camera'),
                            style: ElevatedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 12,
                              ),
                            ),
                          ),
                          ElevatedButton.icon(
                            onPressed:
                                _isProcessing || _image == null
                                    ? null
                                    : _processImage,
                            icon: const Icon(Icons.auto_awesome),
                            label: const Text('Process to 3D'),
                            style: ElevatedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 12,
                              ),
                              backgroundColor: Colors.green,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Processing indicator and results
                    if (_isProcessing)
                      Column(
                        children: [
                          const CircularProgressIndicator(),
                          const SizedBox(height: 16),
                          Text(
                            _resultText,
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      )
                    else if (_resultText.isNotEmpty)
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.blue.shade200),
                        ),
                        child: Text(
                          _resultText,
                          style: const TextStyle(fontSize: 16),
                          textAlign: TextAlign.center,
                        ),
                      ),
                    const SizedBox(height: 24),

                    // Output files list
                    if (_outputFiles.isNotEmpty)
                      Container(
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.05),
                              blurRadius: 5,
                              spreadRadius: 1,
                            ),
                          ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Padding(
                              padding: const EdgeInsets.all(16.0),
                              child: Row(
                                children: [
                                  const Icon(
                                    Icons.folder_open,
                                    color: Colors.blue,
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Result Files (${_outputFiles.length})',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 18,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const Divider(height: 1),
                            ListView.builder(
                              shrinkWrap: true,
                              physics: const NeverScrollableScrollPhysics(),
                              itemCount: _outputFiles.length,
                              itemBuilder: (context, index) {
                                final file = _outputFiles[index];
                                return Card(
                                  margin: const EdgeInsets.symmetric(
                                    horizontal: 8,
                                    vertical: 4,
                                  ),
                                  child: ListTile(
                                    leading: Icon(
                                      Icons.description,
                                      color:
                                          file.endsWith('.obj')
                                              ? Colors.green
                                              : Colors.blue,
                                    ),
                                    title: Text(
                                      path.basename(file),
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                    subtitle: Text(
                                      file,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    trailing: const Icon(Icons.file_open),
                                    onTap: () {
                                      // Handle file opening if needed
                                    },
                                  ),
                                );
                              },
                            ),
                            const SizedBox(height: 8),
                          ],
                        ),
                      ),

                    // Add padding at the bottom for the floating button
                    const SizedBox(height: 100),
                  ],
                ),
              ),
            ),

            // External browser button
            Positioned(
              bottom: 20,
              left: 20,
              right: 20,
              child: ElevatedButton.icon(
                onPressed: _hasProcessedImage ? _openExternalBrowser : null,
                icon: const Icon(Icons.open_in_browser, size: 24),
                label: const Text(
                  'View in 3Dimension',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.deepPurple,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 15,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  elevation: 4,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// WebView Screen for web-based viewing (kept for reference)
class WebViewScreen extends StatefulWidget {
  final String url;

  const WebViewScreen({super.key, required this.url});

  @override
  State<WebViewScreen> createState() => _WebViewScreenState();
}

class _WebViewScreenState extends State<WebViewScreen> {
  late final WebViewController controller;
  bool isLoading = true;
  String errorMessage = '';

  @override
  void initState() {
    super.initState();

    controller =
        WebViewController()
          ..setJavaScriptMode(JavaScriptMode.unrestricted)
          ..setBackgroundColor(const Color(0x00000000))
          ..setNavigationDelegate(
            NavigationDelegate(
              onPageStarted: (String url) {
                setState(() {
                  isLoading = true;
                  errorMessage = '';
                });
                print("WebView loading started: $url");
              },
              onPageFinished: (String url) {
                setState(() {
                  isLoading = false;
                });
                print("WebView loading finished: $url");

                controller
                    .runJavaScriptReturningResult(
                      'document.body.innerHTML.length',
                    )
                    .then((result) {
                      print("Page content length: $result");
                      if (result.toString() == '0') {
                        setState(() {
                          errorMessage =
                              'The page loaded but appears to be empty';
                        });
                      }
                    })
                    .catchError((e) {
                      print("JavaScript error: $e");
                    });
              },
              onWebResourceError: (WebResourceError error) {
                print(
                  "WebView Error: ${error.description} - ${error.errorCode} - ${error.errorType}",
                );
                setState(() {
                  isLoading = false;
                  errorMessage = 'Error: ${error.description}';
                });
              },
              onNavigationRequest: (NavigationRequest request) {
                print("Navigation request to: ${request.url}");
                return NavigationDecision.navigate;
              },
            ),
          )
          ..loadRequest(Uri.parse(widget.url));

    Future.delayed(const Duration(seconds: 1), () {
      print("WebView initialized, URL: ${widget.url}");
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('3D Object Viewer (Web)'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () {
              showDialog(
                context: context,
                builder:
                    (context) => AlertDialog(
                      title: const Text('WebView Information'),
                      content: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('URL: ${widget.url}'),
                          const SizedBox(height: 8),
                          Text('Loading: $isLoading'),
                          const SizedBox(height: 8),
                          Text('Error: $errorMessage'),
                        ],
                      ),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context),
                          child: const Text('Close'),
                        ),
                      ],
                    ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              setState(() {
                isLoading = true;
                errorMessage = '';
              });
              controller.reload();
              print("Reloading WebView");
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: controller, key: const ValueKey('webview')),
          if (isLoading)
            Container(
              color: Colors.white70,
              child: const Center(child: CircularProgressIndicator()),
            ),
          if (errorMessage.isNotEmpty)
            Container(
              color: Colors.black12,
              padding: const EdgeInsets.all(16),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.error_outline,
                      color: Colors.red,
                      size: 48,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      errorMessage,
                      style: const TextStyle(fontSize: 16),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'The page may have SSL certificate issues or be unavailable.',
                      style: TextStyle(fontSize: 14),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
