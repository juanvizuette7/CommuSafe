import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

class CommuSafeAnimatedBackground extends StatefulWidget {
  const CommuSafeAnimatedBackground({
    super.key,
    required this.child,
    this.dark = true,
    this.padding = EdgeInsets.zero,
  });

  final Widget child;
  final bool dark;
  final EdgeInsetsGeometry padding;

  @override
  State<CommuSafeAnimatedBackground> createState() =>
      _CommuSafeAnimatedBackgroundState();
}

class _CommuSafeAnimatedBackgroundState
    extends State<CommuSafeAnimatedBackground>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 12),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (BuildContext context, Widget? child) {
        return CustomPaint(
          painter: _CommuSafeBackgroundPainter(
            progress: _controller.value,
            dark: widget.dark,
          ),
          child: child,
        );
      },
      child: Padding(padding: widget.padding, child: widget.child),
    );
  }
}

class _CommuSafeBackgroundPainter extends CustomPainter {
  const _CommuSafeBackgroundPainter({
    required this.progress,
    required this.dark,
  });

  final double progress;
  final bool dark;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final baseGradient = LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: dark
          ? const <Color>[
              AppColors.primary,
              AppColors.secondary,
              AppColors.accent,
            ]
          : const <Color>[
              Color(0xFFF8FAFC),
              Color(0xFFEFF6FF),
              Color(0xFFFFF1F2),
            ],
    );
    canvas.drawRect(rect, Paint()..shader = baseGradient.createShader(rect));

    _drawRouteLines(canvas, size);
    _drawWindowGrid(canvas, size);
    _drawScanner(canvas, size);
  }

  void _drawRouteLines(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.2
      ..strokeCap = StrokeCap.round
      ..color = (dark ? Colors.white : AppColors.primary).withValues(
        alpha: dark ? 0.12 : 0.08,
      );

    final accentPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round
      ..color = AppColors.danger.withValues(alpha: dark ? 0.20 : 0.13);

    final drift = math.sin(progress * math.pi * 2) * 18;
    for (var i = -2; i < 8; i++) {
      final y = size.height * (i / 7) + drift;
      final path = Path()
        ..moveTo(-30, y)
        ..cubicTo(
          size.width * 0.25,
          y + 72,
          size.width * 0.55,
          y - 56,
          size.width + 36,
          y + 22,
        );
      canvas.drawPath(path, i.isEven ? paint : accentPaint);
    }
  }

  void _drawWindowGrid(Canvas canvas, Size size) {
    final paint = Paint()
      ..style = PaintingStyle.fill
      ..color = (dark ? Colors.white : AppColors.primary).withValues(
        alpha: dark ? 0.065 : 0.045,
      );

    final pulse = 0.45 + math.sin(progress * math.pi * 2) * 0.12;
    final cols = (size.width / 52).ceil();
    final rows = (size.height / 76).ceil();

    for (var row = 0; row < rows; row++) {
      for (var col = 0; col < cols; col++) {
        if ((row + col) % 3 == 1) {
          continue;
        }
        final left = col * 52.0 + ((row % 2) * 18);
        final top = row * 76.0 + 12;
        final width = 20.0 + ((row + col) % 2) * 12;
        final height = 5.0 + pulse * 4;
        final radius = Radius.circular(height / 2);
        canvas.drawRRect(
          RRect.fromRectAndRadius(
            Rect.fromLTWH(left, top, width, height),
            radius,
          ),
          paint,
        );
      }
    }
  }

  void _drawScanner(Canvas canvas, Size size) {
    final sweepTop = (size.height + 160) * progress - 80;
    final scannerRect = Rect.fromLTWH(0, sweepTop, size.width, 90);
    final paint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: <Color>[
          Colors.transparent,
          AppColors.success.withValues(alpha: dark ? 0.10 : 0.08),
          Colors.transparent,
        ],
      ).createShader(scannerRect);

    canvas.drawRect(scannerRect, paint);

    final linePaint = Paint()
      ..strokeWidth = 1.4
      ..color = AppColors.success.withValues(alpha: dark ? 0.22 : 0.16);
    canvas.drawLine(
      Offset(0, sweepTop + 45),
      Offset(size.width, sweepTop + 45),
      linePaint,
    );
  }

  @override
  bool shouldRepaint(covariant _CommuSafeBackgroundPainter oldDelegate) {
    return oldDelegate.progress != progress || oldDelegate.dark != dark;
  }
}
