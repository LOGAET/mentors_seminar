# Итоговое задание по модулю 1 — Go

Mentor's Seminar, тема 3 «Go разработка». Каждое задание лежит в отдельной папке и запускается как самостоятельная программа.

| № | Папка | Задание |
|---|-------|---------|
| 1 | [`task01_calculator`](task01_calculator) | Калькулятор с проверкой деления на ноль |
| 2 | [`task02_number_analysis`](task02_number_analysis) | Анализ числа: знак, чётность, делимость на 3 и 5 |
| 3 | [`task03_sum_average`](task03_sum_average) | Сумма и среднее от 1 до N |
| 4 | [`task04_multiplication_table`](task04_multiplication_table) | Таблица умножения через функцию `printTable(n)` |
| 5 | [`task05_min_max`](task05_min_max) | Максимум и минимум из N чисел |
| 6 | [`task06_sign_count`](task06_sign_count) | Количество положительных, отрицательных чисел и нулей |
| 7 | [`task07_filtered_sum`](task07_filtered_sum) | Сумма чисел от 1 до N, которые чётные и делятся на 3 |
| 8 | [`task08_prime`](task08_prime) | Проверка простого числа, функция `isPrime(n int) bool` |
| 9 | [`task09_atm`](task09_atm) | Мини-банкомат: баланс, пополнение, снятие с проверкой средств |
| 10 | [`task10_statistics`](task10_statistics) | Статистика последовательности |

## Запуск

Нужен Go 1.21+.

```bash
go run ./task01_calculator
go run ./task09_atm
```

Во всех программах ввод проверяется: при некорректном значении программа сообщает об ошибке и просит ввести его снова.
