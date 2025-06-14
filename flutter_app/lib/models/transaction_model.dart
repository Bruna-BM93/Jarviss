import 'package:flutter/foundation.dart';

class Transaction {
  final int? id;
  final String descricao;
  final double valor;
  final String tipo; // 'receita' ou 'despesa'
  final String data; // Formato 'YYYY-MM-DD'

  Transaction({
    this.id,
    required this.descricao,
    required this.valor,
    required this.tipo,
    required this.data,
  }) {
    if (tipo != 'receita' && tipo != 'despesa') {
      throw ArgumentError("Tipo deve ser 'receita' ou 'despesa'");
    }
    // Adicionar validação de formato de data se necessário,
    // mas o backend já faz isso.
  }

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id'] as int?,
      descricao: json['descricao'] as String,
      valor: (json['valor'] as num).toDouble(), // Backend retorna REAL, pode ser int ou double
      tipo: json['tipo'] as String,
      data: json['data'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> dataMap = {
      'descricao': descricao,
      'valor': valor,
      'tipo': tipo,
      'data': data,
    };
    if (id != null) {
      dataMap['id'] = id; // Incluir ID apenas se não for nulo (para atualizações futuras)
                          // Para criação, o backend atribui o ID.
                          // A especificação diz para omitir se nulo, então não precisa incluir 'id': null.
    }
    return dataMap;
  }

  // Para facilitar o debug e visualização
  @override
  String toString() {
    return 'Transaction{id: $id, descricao: $descricao, valor: $valor, tipo: $tipo, data: $data}';
  }
}
