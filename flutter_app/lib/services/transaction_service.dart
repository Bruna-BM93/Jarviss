import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/transaction_model.dart'; // Importa o modelo de transação

class TransactionService {
  // Use http://10.0.2.2:5000 para o emulador Android acessar o localhost do host.
  // Para iOS ou dispositivo físico, ajuste o IP.
  static const String _baseUrl = 'http://10.0.2.2:5000';

  Future<List<Transaction>> getTransactions(String token) async {
    final url = Uri.parse('$_baseUrl/transacoes');

    try {
      final response = await http.get(
        url,
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> jsonData = jsonDecode(utf8.decode(response.bodyBytes));
        return jsonData.map((item) => Transaction.fromJson(item)).toList();
      } else {
        String errorMessage = _extractErrorMessage(response);
        throw Exception('Falha ao buscar transações: ${response.statusCode} - $errorMessage');
      }
    } catch (e) {
      // Se for uma exceção de rede ou outra não relacionada à resposta HTTP
      throw Exception('Falha ao conectar ao serviço de transações: $e');
    }
  }

  Future<Transaction> addTransaction(Transaction transaction, String token) async {
    final url = Uri.parse('$_baseUrl/transacoes');

    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(transaction.toJson()),
      );

      if (response.statusCode == 201) { // Backend retorna 201 para criação bem-sucedida
        final dynamic jsonData = jsonDecode(utf8.decode(response.bodyBytes));
        return Transaction.fromJson(jsonData);
      } else {
        String errorMessage = _extractErrorMessage(response);
        throw Exception('Falha ao adicionar transação: ${response.statusCode} - $errorMessage');
      }
    } catch (e) {
      throw Exception('Falha ao conectar ao serviço para adicionar transação: $e');
    }
  }

  // Função auxiliar para tentar extrair a mensagem de erro do JSON do backend
  String _extractErrorMessage(http.Response response) {
    try {
      final errorData = jsonDecode(utf8.decode(response.bodyBytes));
      if (errorData['erro'] != null) {
        return errorData['erro'];
      }
    } catch (e) {
      // Se não for JSON ou não tiver a chave 'erro', retorna o corpo bruto
    }
    return response.body;
  }
}
