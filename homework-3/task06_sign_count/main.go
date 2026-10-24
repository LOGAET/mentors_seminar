// Задание 6. Количество положительных и отрицательных чисел.
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
		os.Exit(1)
	}
	return strings.TrimSpace(line)
}

func readCount(prompt string) int {
	for {
		v, err := strconv.Atoi(readLine(prompt))
		if err == nil && v >= 1 {
			return v
		}
		fmt.Println("Ошибка: введите целое число не меньше 1.")
	}
}

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

func main() {
	n := readCount("Сколько чисел будет введено? N = ")

	positive, negative, zeros := 0, 0, 0
	for i := 1; i <= n; i++ {
		x := readFloat(fmt.Sprintf("Число %d: ", i))
		if x > 0 {
			positive++
		} else if x < 0 {
			negative++
		} else {
			zeros++
		}
	}

	fmt.Println("Положительных чисел:", positive)
	fmt.Println("Отрицательных чисел:", negative)
	fmt.Println("Нулей:", zeros)
}
