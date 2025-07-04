import 'package:flutter/material.dart';

import 'financial_chart.dart';
import 'goal_card.dart';
import 'bank_notifications.dart';

void main() {
  runApp(const JarvissApp());
}

class JarvissApp extends StatelessWidget {
  const JarvissApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: DashboardScreen(),
    );
  }
}

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Jarviss Dashboard')),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const FinancialChart(),
            const Padding(
              padding: EdgeInsets.all(16.0),
              child: Text('Notificações Bancárias',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            ...BankNotificationService.simulateIncomingNotifications()
                .map((n) => ListTile(title: Text(n)))
                .toList(),
            const Padding(
              padding: EdgeInsets.all(16.0),
              child: Text('Metas Financeiras',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            const GoalCard(
              title: 'Faturamento Mensal',
              current: 5200,
              target: 10000,
            ),
            const GoalCard(
              title: 'Reduzir Gastos',
              current: 3700,
              target: 5000,
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

