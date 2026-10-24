// Задание 3. Сумма и среднее от 1 до N.
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

var reader = bufio.NewReader(os.Stdin)

// readPositiveInt просит ввести число >= 1.
func readPositiveInt(prompt string) int {
	for {
		fmt.Print(prompt)
		line, err := reader.ReadString('\n')
		if err != nil && line == "" {
			fmt.Println("\nВвод завершён.")
			os.Exit(1)
		}
		v, err := strconv.Atoi(strings.TrimSpace(line))
		if err == nil && v >= 1 {
			return v
		}
		fmt.Println("Ошибка: введите целое число не меньше 1.")
	}
}

func main() {
	n := readPositiveInt("Введите число N: ")

	sum := 0
	for i := 1; i <= n; i++ {
		sum += i
	}
	average := float64(sum) / float64(n)

	fmt.Printf("Сумма чисел от 1 до %d: %d\n", n, sum)
	fmt.Printf("Среднее значение: %.2f\n", average)
}
