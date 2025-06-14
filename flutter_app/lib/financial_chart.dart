import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class FinancialChart extends StatelessWidget {
  const FinancialChart({super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Gráfico Financeiro',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 200, child: LineChart(_sampleData())),
          ],
        ),
      ),
    );
  }

  LineChartData _sampleData() {
    return LineChartData(
      gridData: FlGridData(show: true),
      titlesData: FlTitlesData(show: true),
      borderData: FlBorderData(show: true),
      lineBarsData: [
        LineChartBarData(
          spots: const [
            FlSpot(1, 3000),
            FlSpot(2, 4000),
            FlSpot(3, 5000),
            FlSpot(4, 6000),
            FlSpot(5, 7500),
          ],
          isCurved: true,
          color: Colors.green,
          barWidth: 3,
        ),
        LineChartBarData(
          spots: const [
            FlSpot(1, 1000),
            FlSpot(2, 2000),
            FlSpot(3, 3000),
            FlSpot(4, 3500),
            FlSpot(5, 3700),
          ],
          isCurved: true,
          color: Colors.red,
          barWidth: 3,
        ),
      ],
    );
  }
}
