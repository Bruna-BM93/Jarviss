// Importa o pacote mockito e a classe que queremos mockar.
import 'package:mockito/annotations.dart';
import 'package:jarviss_app/services/ia_service.dart'; // Ajuste o caminho conforme necessário

// Anotação para gerar o mock para IaService.
// O build_runner procurará por esta anotação.
@GenerateMocks([IaService])
void main() {
  // Este arquivo não precisa fazer nada além de conter as anotações.
  // O build_runner fará o resto.
}
