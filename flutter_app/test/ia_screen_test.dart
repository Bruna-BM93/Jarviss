import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:jarviss_app/screens/ia_screen.dart';
import 'package:jarviss_app/services/ia_service.dart'; // Necessário para o tipo no mock
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';

// Importa o arquivo de mock gerado.
// O nome do arquivo gerado será o nome do arquivo que contém @GenerateMocks + ".mocks.dart"
// Neste caso, se mocks.dart contém @GenerateMocks([IaService]), ele gerará mocks.mocks.dart
// E dentro dele teremos a classe MockIaService.
import 'mocks.mocks.dart'; // Atualizado para o nome do arquivo que contém @GenerateMocks

// Não precisamos mais desta anotação aqui se ela estiver em mocks.dart
// @GenerateMocks([IaService])

void main() {
  late MockIaService mockIaService; // Use o tipo gerado pelo mockito

  setUp(() {
    mockIaService = MockIaService(); // Inicializa o mock
  });

  testWidgets('IaScreen renders basic elements', (WidgetTester tester) async {
    // Envolve IaScreen com MaterialApp para fornecer o contexto necessário.
    // Fornecendo o mockIaService para a IaScreen.
    await tester.pumpWidget(MaterialApp(home: IaScreen(iaService: mockIaService)));

    expect(find.text('Perguntar à IA'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
    expect(find.widgetWithText(ElevatedButton, 'Enviar Pergunta'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
  });

  testWidgets('IaScreen shows CircularProgressIndicator and then response on success', (WidgetTester tester) async {
    const String pergunta = 'Qual a cor do céu?';
    const String respostaSimulada = 'Azul, geralmente.';

    // Configura o mock para retornar uma resposta quando chamado
    when(mockIaService.perguntarIA(pergunta, any)) // 'any' para o token
        .thenAnswer((_) async => respostaSimulada);

    await tester.pumpWidget(MaterialApp(home: IaScreen(iaService: mockIaService)));

    // Simula a digitação no TextField
    await tester.enterText(find.byType(TextField), pergunta);

    // Simula o toque no botão "Enviar Pergunta"
    await tester.tap(find.widgetWithText(ElevatedButton, 'Enviar Pergunta'));
    await tester.pump(); // Inicia a chamada (isLoading = true), reconstrói com o CircularProgressIndicator

    // Verifica o CircularProgressIndicator
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    // Aguarda a conclusão da Future (chamada de serviço mockada) e reconstrução do widget
    await tester.pumpAndSettle();

    // Verifica se o indicador de progresso sumiu e a resposta apareceu
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.text(respostaSimulada), findsOneWidget);
  });

  testWidgets('IaScreen shows error message on failure', (WidgetTester tester) async {
    const String pergunta = 'Isso vai falhar?';
    const String erroSimulado = 'Falha simulada na IA';

    // Configura o mock para lançar uma exceção
    when(mockIaService.perguntarIA(pergunta, any))
        .thenThrow(Exception(erroSimulado));

    await tester.pumpWidget(MaterialApp(home: IaScreen(iaService: mockIaService)));

    await tester.enterText(find.byType(TextField), pergunta);
    await tester.tap(find.widgetWithText(ElevatedButton, 'Enviar Pergunta'));
    await tester.pump(); // Inicia o loading

    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    await tester.pumpAndSettle(); // Completa a Future com erro

    expect(find.byType(CircularProgressIndicator), findsNothing);
    // A mensagem de erro é atribuída a _respostaIa no widget
    expect(find.text('Erro: Exception: $erroSimulado'), findsOneWidget);
  });
}
