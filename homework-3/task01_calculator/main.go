// Задание 1. Калькулятор с проверкой.
package main

import (
	"bufio"
	"errors"
	"fmt"
	"os"
	"strconv"
	"strings"
)

var reader = bufio.NewReader(os.Stdin)

// readLine читает строку ввода.
func readLine(prompt string) string {
	fmt.Print(prompt)
	line, err := reader.ReadString('\n')
	if err != nil && line == "" {
		fmt.Println("\nВвод завершён.")
		os.Exit(1)
	}
	return strings.TrimSpace(line)
}

// readFloat просит ввести число, пока ввод не корректен.
func readFloat(prompt string) float64 {
	for {
		s := strings.ReplaceAll(readLine(prompt), ",", ".")
		v, err := strconv.ParseFloat(s, 64)
		if err == nil {
			return v
		}
		fmt.Println("Ошибка: введите число.")
	}
}

// calculate выполняет операцию над a и b.
func calculate(a, b float64, op string) (float64, error) {
	switch op {
	case "+":
		return a + b, nil
	case "-":
		return a - b, nil
	case "*":
		return a * b, nil
	case "/":
		if b == 0 {
			return 0, errors.New("деление на ноль невозможно")
		}
		return a / b, nil
	default:
		return 0, fmt.Errorf("неизвестная операция %q", op)
	}
}

func main() {
	a := readFloat("Введите первое число: ")
	b := readFloat("Введите второе число: ")

	var op string
	for {
		op = readLine("Введите операцию (+, -, *, /): ")
		if op == "+" || op == "-" || op == "*" || op == "/" {
			break
		}
		fmt.Println("Ошибка: допустимы только +, -, *, /.")
	}

	result, err := calculate(a, b, op)
	if err != nil {
		fmt.Println("Ошибка:", err)
		return
	}
	fmt.Printf("%g %s %g = %g\n", a, op, b, result)
}
