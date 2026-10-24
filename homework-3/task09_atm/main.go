// Задание 9. Мини-банкомат.
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

var reader = bufio.NewReader(os.Stdin)

func readLine(prompt string) string {
	fmt.Print(prompt)
	line, err := reader.ReadString('\n')
	if err != nil && line == "" {
		fmt.Println("\nВвод завершён.")
		os.Exit(0)
	}
	return strings.TrimSpace(line)
}

// readAmount просит ввести сумму (0 допустим только при allowZero).
func readAmount(prompt string, allowZero bool) float64 {
	for {
		s := strings.ReplaceAll(readLine(prompt), ",", ".")
		v, err := strconv.ParseFloat(s, 64)
		switch {
		case err != nil:
			fmt.Println("Ошибка: введите число.")
		case v < 0, v == 0 && !allowZero:
			fmt.Println("Ошибка: сумма должна быть положительной.")
		default:
			return v
		}
	}
}

func main() {
	balance := readAmount("Введите начальный баланс: ", true)

	for {
		fmt.Println()
		fmt.Println("Выберите действие:")
		fmt.Println("1. Посмотреть баланс")
		fmt.Println("2. Пополнить баланс")
		fmt.Println("3. Снять средства")
		fmt.Println("0. Выход")

		switch readLine("Ваш выбор: ") {
		case "1":
			fmt.Printf("Текущий баланс: %.2f\n", balance)
		case "2":
			amount := readAmount("Сумма пополнения: ", false)
			balance += amount
			fmt.Printf("Баланс пополнен на %.2f. Текущий баланс: %.2f\n", amount, balance)
		case "3":
			amount := readAmount("Сумма снятия: ", false)
			if amount > balance {
				fmt.Printf("Недостаточно средств: на балансе %.2f, запрошено %.2f.\n", balance, amount)
			} else {
				balance -= amount
				fmt.Printf("Выдано %.2f. Текущий баланс: %.2f\n", amount, balance)
			}
		case "0":
			fmt.Println("Спасибо, до свидания!")
			return
		default:
			fmt.Println("Неизвестная команда, выберите 0–3.")
		}
	}
}
