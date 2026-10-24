// Задание 2. Анализ числа.
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

var reader = bufio.NewReader(os.Stdin)

// readInt просит ввести целое число.
func readInt(prompt string) int {
	for {
		fmt.Print(prompt)
		line, err := reader.ReadString('\n')
		if err != nil && line == "" {
			fmt.Println("\nВвод завершён.")
			os.Exit(1)
		}
		v, err := strconv.Atoi(strings.TrimSpace(line))
		if err == nil {
			return v
		}
		fmt.Println("Ошибка: введите целое число.")
	}
}

func main() {
	n := readInt("Введите число N: ")

	// Знак числа
	if n > 0 {
		fmt.Println("Число положительное.")
	} else if n < 0 {
		fmt.Println("Число отрицательное.")
	} else {
		fmt.Println("Число равно нулю (ни положительное, ни отрицательное).")
	}

	// Чётность
	if n%2 == 0 {
		fmt.Println("Число чётное.")
	} else {
		fmt.Println("Число нечётное.")
	}

	// Делимость на 3 и на 5
	by3 := n%3 == 0
	by5 := n%5 == 0
	if by3 {
		fmt.Println("Делится на 3: да.")
	} else {
		fmt.Println("Делится на 3: нет.")
	}
	if by5 {
		fmt.Println("Делится на 5: да.")
	} else {
		fmt.Println("Делится на 5: нет.")
	}
	if by3 && by5 {
		fmt.Println("Число делится и на 3, и на 5 (то есть на 15).")
	}
}
