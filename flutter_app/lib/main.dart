import 'package:flutter/material.dart';

import 'financial_chart.dart';
import 'goal_card.dart';
// import 'bank_notifications.dart'; // Removido
import 'screens/ia_screen.dart';
import 'screens/transaction_list_screen.dart';
import 'screens/interpret_notification_screen.dart'; // Importa a nova tela

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
            ListTile( // Adiciona o ListTile para a tela de IA
              leading: const Icon(Icons.psychology), // Ícone de IA
              title: const Text('Assistente de IA'),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const IaScreen()),
                );
              },
            ),
            ListTile( // Adiciona o ListTile para a tela de Transações
              leading: const Icon(Icons.account_balance_wallet),
              title: const Text('Minhas Transações'),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const TransactionListScreen()),
                );
              },
            ),
            // ListTile de Notificações Bancárias Modificado
            ListTile(
              leading: const Icon(Icons.receipt_long), // Ícone para interpretação
              title: const Text('Interpretar Notificação Bancária'),
              subtitle: const Text('Cole o texto da sua notificação para análise por IA'),
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const InterpretNotificationScreen()),
                );
              },
            ),
            // Removida a lista de notificações simuladas
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

