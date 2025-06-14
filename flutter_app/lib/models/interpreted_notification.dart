class InterpretedNotification {
  final String? tipo;
  final double? valor;
  final String? descricaoSugerida;

  InterpretedNotification({
    this.tipo,
    this.valor,
    this.descricaoSugerida,
  });

  factory InterpretedNotification.fromJson(Map<String, dynamic> json) {
    return InterpretedNotification(
      tipo: json['tipo'] as String?,
      // O backend pode retornar valor como int ou double, então tratamos como num.
      // Se for null, permanece null. Caso contrário, converte para double.
      valor: json['valor'] == null ? null : (json['valor'] as num).toDouble(),
      descricaoSugerida: json['descricao_sugerida'] as String?,
    );
  }

  // Para facilitar o debug
  @override
  String toString() {
    return 'InterpretedNotification{tipo: $tipo, valor: $valor, descricaoSugerida: $descricaoSugerida}';
  }
}
