import 'package:flutter/material.dart';
import '../services/ia_service.dart'; // Importa o serviço de IA

class IaScreen extends StatefulWidget {
  final IaService? iaService; // Permite injetar o serviço para testes

  const IaScreen({super.key, this.iaService});

  @override
  State<IaScreen> createState() => _IaScreenState();
}

class _IaScreenState extends State<IaScreen> {
  final TextEditingController _perguntaController = TextEditingController();
  String _respostaIa = '';
  bool _isLoading = false;
  late final IaService _iaService; // Será inicializado no initState

  @override
  void initState() {
    super.initState();
    _iaService = widget.iaService ?? IaService(); // Usa o serviço injetado ou um novo
  }

  Future<void> _enviarPergunta() async {
    if (_perguntaController.text.isEmpty) {
      setState(() {
        _respostaIa = 'Por favor, digite uma pergunta.';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _respostaIa = ''; // Limpa a resposta anterior
    });

    try {
      // TODO: Substituir por um token JWT real obtido após o login
      const String tokenSimulado = "SIMULATED_VALID_JWT_TOKEN";
      final resposta = await _iaService.perguntarIA(_perguntaController.text, tokenSimulado);
      setState(() {
        _respostaIa = resposta;
      });
    } catch (e) {
      setState(() {
        _respostaIa = 'Erro: ${e.toString()}';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  void dispose() {
    _perguntaController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Perguntar à IA'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            TextField(
              controller: _perguntaController,
              decoration: const InputDecoration(
                labelText: 'Digite sua pergunta',
                border: OutlineInputBorder(),
              ),
              minLines: 1,
              maxLines: 5,
            ),
            const SizedBox(height: 16.0),
            ElevatedButton(
              onPressed: _isLoading ? null : _enviarPergunta,
              child: const Text('Enviar Pergunta'),
            ),
            const SizedBox(height: 24.0),
            if (_isLoading)
              const Center(child: CircularProgressIndicator())
            else if (_respostaIa.isNotEmpty)
              Expanded(
                child: SingleChildScrollView(
                  child: Container(
                    padding: const EdgeInsets.all(12.0),
                    decoration: BoxDecoration(
                      color: Colors.grey[200],
                      borderRadius: BorderRadius.circular(8.0),
                    ),
                    child: Text(
                      _respostaIa,
                      style: const TextStyle(fontSize: 16.0),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
