import 'package:flutter/material.dart';
import 'package:intl/intl.dart'; // Para formatação de data
import '../models/transaction_model.dart';
import '../services/transaction_service.dart';

class AddEditTransactionScreen extends StatefulWidget {
  final Transaction? transactionToEdit; // Opcional, para edição

  const AddEditTransactionScreen({super.key, this.transactionToEdit});

  @override
  State<AddEditTransactionScreen> createState() => _AddEditTransactionScreenState();
}

class _AddEditTransactionScreenState extends State<AddEditTransactionScreen> {
  final _formKey = GlobalKey<FormState>();
  final TransactionService _transactionService = TransactionService();

  late TextEditingController _descricaoController;
  late TextEditingController _valorController;
  late TextEditingController _dataController;
  String _selectedType = 'despesa';
  DateTime _selectedDate = DateTime.now();
  bool _isLoading = false;

  // TODO: Substituir por um token JWT real obtido após o login
  static const String _simulatedToken = "SIMULATED_VALID_JWT_TOKEN";

  @override
  void initState() {
    super.initState();
    _descricaoController = TextEditingController(text: widget.transactionToEdit?.descricao);
    _valorController = TextEditingController(text: widget.transactionToEdit?.valor.toString());
    _selectedType = widget.transactionToEdit?.tipo ?? 'despesa';

    if (widget.transactionToEdit != null) {
      try {
        _selectedDate = DateFormat('yyyy-MM-dd').parse(widget.transactionToEdit!.data);
      } catch (e) {
        _selectedDate = DateTime.now(); // Fallback
      }
    }
    _dataController = TextEditingController(text: DateFormat('yyyy-MM-dd').format(_selectedDate));
  }

  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2101),
    );
    if (picked != null && picked != _selectedDate) {
      setState(() {
        _selectedDate = picked;
        _dataController.text = DateFormat('yyyy-MM-dd').format(_selectedDate);
      });
    }
  }

  Future<void> _submitForm() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);

      final newTransaction = Transaction(
        // id: widget.transactionToEdit?.id, // Backend atribui ID na criação
        descricao: _descricaoController.text,
        valor: double.parse(_valorController.text),
        tipo: _selectedType,
        data: _dataController.text,
      );

      try {
        if (widget.transactionToEdit == null) {
          await _transactionService.addTransaction(newTransaction, _simulatedToken);
        } else {
          // TODO: Implementar lógica de atualização (PUT request no serviço)
          // Por enquanto, vamos apenas simular sucesso para fechar a tela
          print("Lógica de atualização a ser implementada para ID: ${widget.transactionToEdit!.id}");
        }

        if (mounted) {
          Navigator.pop(context, true); // Retorna true para indicar sucesso e recarregar
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Erro ao salvar transação: ${e.toString()}')),
          );
        }
      } finally {
        if (mounted) {
          setState(() => _isLoading = false);
        }
      }
    }
  }

  @override
  void dispose() {
    _descricaoController.dispose();
    _valorController.dispose();
    _dataController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.transactionToEdit == null ? 'Nova Transação' : 'Editar Transação'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    TextFormField(
                      controller: _descricaoController,
                      decoration: const InputDecoration(labelText: 'Descrição'),
                      validator: (value) => value == null || value.isEmpty ? 'Campo obrigatório' : null,
                    ),
                    TextFormField(
                      controller: _valorController,
                      decoration: const InputDecoration(labelText: 'Valor (R\$)'),
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      validator: (value) {
                        if (value == null || value.isEmpty) return 'Campo obrigatório';
                        if (double.tryParse(value) == null) return 'Valor inválido';
                        if (double.parse(value) <= 0) return 'Valor deve ser positivo';
                        return null;
                      },
                    ),
                    DropdownButtonFormField<String>(
                      value: _selectedType,
                      decoration: const InputDecoration(labelText: 'Tipo'),
                      items: ['despesa', 'receita'].map((String value) {
                        return DropdownMenuItem<String>(
                          value: value,
                          child: Text(value == 'despesa' ? 'Despesa' : 'Receita'),
                        );
                      }).toList(),
                      onChanged: (String? newValue) {
                        setState(() {
                          _selectedType = newValue!;
                        });
                      },
                    ),
                    TextFormField(
                      controller: _dataController,
                      decoration: const InputDecoration(labelText: 'Data'),
                      readOnly: true,
                      onTap: () => _selectDate(context),
                      validator: (value) => value == null || value.isEmpty ? 'Campo obrigatório' : null,
                    ),
                    const SizedBox(height: 20),
                    ElevatedButton(
                      onPressed: _submitForm,
                      child: const Text('Salvar Transação'),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
