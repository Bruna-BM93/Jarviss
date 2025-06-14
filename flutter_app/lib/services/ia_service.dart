import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/interpreted_notification.dart'; // Importa o novo modelo

class IaService {
  // Use http://10.0.2.2:5000 para o emulador Android acessar o localhost do host.
  // Para iOS ou dispositivo físico, ajuste o IP.
  static const String _baseIaUrl = 'http://10.0.2.2:5000/ia'; // Base URL para endpoints de IA

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
    return response.body; // Retorna o corpo bruto se não puder decodificar ou encontrar 'erro'
  }

  Future<String> perguntarIA(String pergunta, String token) async {
    final url = Uri.parse('$_baseIaUrl/perguntar'); // Ajustado para usar _baseIaUrl

    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({'pergunta': pergunta}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return data['resposta'];
      } else {
        String errorMessage = _extractErrorMessage(response);
        throw Exception('Falha ao perguntar à IA: ${response.statusCode} - $errorMessage');
      }
    } catch (e) {
      throw Exception('Falha ao conectar ao serviço de IA: $e');
    }
  }

  Future<InterpretedNotification> interpretarNotificacao(String textoNotificacao, String token) async {
    final url = Uri.parse('$_baseIaUrl/interpretar_notificacao'); // Novo endpoint

    try {
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({'texto_notificacao': textoNotificacao}),
      );

      if (response.statusCode == 200) {
        final jsonData = jsonDecode(utf8.decode(response.bodyBytes));
        return InterpretedNotification.fromJson(jsonData);
      } else {
        String errorMessage = _extractErrorMessage(response);
        throw Exception('Falha ao interpretar notificação: ${response.statusCode} - $errorMessage');
      }
    } catch (e) {
      throw Exception('Falha ao conectar ao serviço para interpretar notificação: $e');
    }
  }
}
