import 'package:flutter/material.dart';
import 'package:intl/intl.dart'; // Para formatar a data ao lançar transação
import '../models/interpreted_notification.dart';
import '../models/transaction_model.dart' as t_model; // Alias para evitar conflito de nome
import '../services/ia_service.dart';
import '../services/transaction_service.dart';

class InterpretNotificationScreen extends StatefulWidget {
  const InterpretNotificationScreen({super.key});

  @override
  State<InterpretNotificationScreen> createState() => _InterpretNotificationScreenState();
}

class _InterpretNotificationScreenState extends State<InterpretNotificationScreen> {
  final TextEditingController _notificationTextController = TextEditingController();
  final IaService _iaService = IaService();
  final TransactionService _transactionService = TransactionService();

  InterpretedNotification? _interpretedData;
  bool _isLoadingInterpretation = false;
  bool _isLoadingTransaction = false;
  String? _errorMessage;

  // TODO: Substituir por um token JWT real obtido após o login
  static const String _simulatedToken = "SIMULATED_VALID_JWT_TOKEN";

  Future<void> _analisarNotificacao() async {
    if (_notificationTextController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Por favor, cole o texto da notificação.')),
      );
      return;
    }

    setState(() {
      _isLoadingInterpretation = true;
      _interpretedData = null; // Limpa dados anteriores
      _errorMessage = null;
    });

    try {
      final result = await _iaService.interpretarNotificacao(
        _notificationTextController.text,
        _simulatedToken,
      );
      setState(() {
        _interpretedData = result;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Erro ao analisar: ${e.toString()}';
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(_errorMessage!)),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingInterpretation = false;
        });
      }
    }
  }

  Future<void> _lancarTransacao() async {
    if (_interpretedData == null ||
        _interpretedData!.tipo == null ||
        _interpretedData!.valor == null ||
        _interpretedData!.descricaoSugerida == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Dados interpretados insuficientes para lançar a transação.')),
      );
      return;
    }

    // Validação adicional do tipo
    if (_interpretedData!.tipo! != 'receita' && _interpretedData!.tipo! != 'despesa') {
       ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Tipo de transação inválido: ${_interpretedData!.tipo}')),
      );
      return;
    }

    // Validação adicional do valor
    if (_interpretedData!.valor! <= 0) {
       ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Valor da transação deve ser positivo: ${_interpretedData!.valor}')),
      );
      return;
    }


    setState(() {
      _isLoadingTransaction = true;
    });

    final novaTransacao = t_model.Transaction(
      descricao: _interpretedData!.descricaoSugerida!,
      valor: _interpretedData!.valor!,
      tipo: _interpretedData!.tipo!,
      data: DateFormat('yyyy-MM-dd').format(DateTime.now()), // Data atual
    );

    try {
      await _transactionService.addTransaction(novaTransacao, _simulatedToken);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Transação lançada com sucesso!')),
        );
        // Opcional: Limpar campos ou navegar para outra tela
        _notificationTextController.clear();
        setState(() {
          _interpretedData = null;
        });
        // Navigator.pop(context); // Ou para a lista de transações
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erro ao lançar transação: ${e.toString()}')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingTransaction = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _notificationTextController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Interpretar Notificação'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            const Text(
              'Cole o texto da sua notificação bancária abaixo:',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _notificationTextController,
              maxLines: 5,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'Ex: Pagamento PIX de R\$50.00 para Supermercado ABC...',
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _isLoadingInterpretation ? null : _analisarNotificacao,
              child: _isLoadingInterpretation
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Analisar Notificação'),
            ),
            if (_errorMessage != null && _interpretedData == null) ...[
              const SizedBox(height: 16),
              Text(_errorMessage!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            if (_interpretedData != null) ...[
              const SizedBox(height: 24),
              Text('Dados Interpretados:', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Card(
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Tipo: ${_interpretedData!.tipo ?? "N/A"}'),
                      Text('Valor: R\$ ${_interpretedData!.valor?.toStringAsFixed(2) ?? "N/A"}'),
                      Text('Descrição Sugerida: ${_interpretedData!.descricaoSugerida ?? "N/A"}'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: (_isLoadingTransaction || _interpretedData?.valor == null || _interpretedData?.tipo == null || _interpretedData?.descricaoSugerida == null)
                  ? null
                  : _lancarTransacao,
                style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                child: _isLoadingTransaction
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Lançar Transação'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
