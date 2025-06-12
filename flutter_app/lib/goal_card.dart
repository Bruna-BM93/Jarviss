import 'package:flutter/material.dart';

class GoalCard extends StatelessWidget {
  final String title;
  final double current;
  final double target;

  const GoalCard({super.key, required this.title, required this.current, required this.target});

  @override
  Widget build(BuildContext context) {
    final percent = (current / target).clamp(0.0, 1.0);

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      child: ListTile(
        title: Text(title),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            LinearProgressIndicator(value: percent),
            const SizedBox(height: 4),
            Text('R\$ ${current.toStringAsFixed(2)} / R\$ ${target.toStringAsFixed(2)}'),
          ],
        ),
      ),
    );
  }
}

