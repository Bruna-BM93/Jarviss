import 'package:flutter/material.dart';
import '../models/transaction_model.dart';
import '../services/transaction_service.dart';
import 'add_edit_transaction_screen.dart'; // Será criada a seguir

class TransactionListScreen extends StatefulWidget {
  const TransactionListScreen({super.key});

  @override
  State<TransactionListScreen> createState() => _TransactionListScreenState();
}

class _TransactionListScreenState extends State<TransactionListScreen> {
  List<Transaction> _transactions = [];
  bool _isLoading = true;
  String? _errorMessage;
  final TransactionService _transactionService = TransactionService();

  // TODO: Substituir por um token JWT real obtido após o login
  static const String _simulatedToken = "SIMULATED_VALID_JWT_TOKEN";

  @override
  void initState() {
    super.initState();
    _loadTransactions();
  }

  Future<void> _loadTransactions() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    try {
      final transactions = await _transactionService.getTransactions(_simulatedToken);
      setState(() {
        _transactions = transactions;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _navigateToAdicionarTransacao() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const AddEditTransactionScreen()),
    );

    // Se uma transação foi adicionada com sucesso, recarrega a lista
    if (result == true) {
      _loadTransactions();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Minhas Transações'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadTransactions,
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: _navigateToAdicionarTransacao,
        tooltip: 'Adicionar Transação',
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Text('Erro ao carregar transações:\n$_errorMessage', textAlign: TextAlign.center),
        ),
      );
    }
    if (_transactions.isEmpty) {
      return const Center(child: Text('Nenhuma transação encontrada.'));
    }
    return ListView.builder(
      itemCount: _transactions.length,
      itemBuilder: (context, index) {
        final transaction = _transactions[index];
        final color = transaction.tipo == 'receita' ? Colors.green : Colors.red;
        final sign = transaction.tipo == 'receita' ? '+' : '-';

        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: color,
              child: Text(
                transaction.tipo == 'receita' ? 'R' : 'D',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ),
            title: Text(transaction.descricao),
            subtitle: Text(transaction.data), // Formato YYYY-MM-DD
            trailing: Text(
              '$sign R\$ ${transaction.valor.toStringAsFixed(2)}',
              style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 15),
            ),
            // TODO: Adicionar funcionalidade de onTap para editar/excluir
          ),
        );
      },
    );
  }
}
