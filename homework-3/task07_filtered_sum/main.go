// Задание 7. Сумма только подходящих чисел.
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

func main() {
	reader := bufio.NewReader(os.Stdin)

	var n int
	for {
		fmt.Print("Введите число N: ")
		line, err := reader.ReadString('\n')
		if err != nil && line == "" {
			fmt.Println("\nВвод завершён.")
			return
		}
		v, err := strconv.Atoi(strings.TrimSpace(line))
		if err == nil && v >= 1 {
			n = v
			break
		}
		fmt.Println("Ошибка: введите целое число не меньше 1.")
	}

	sum := 0
	var matched []string
	for i := 1; i <= n; i++ {
		if i%2 == 0 && i%3 == 0 {
			sum += i
			matched = append(matched, strconv.Itoa(i))
		}
	}

	if len(matched) == 0 {
		fmt.Printf("В диапазоне от 1 до %d нет чисел, которые чётные и делятся на 3.\n", n)
		fmt.Println("Сумма: 0")
		return
	}
	fmt.Println("Подходящие числа:", strings.Join(matched, ", "))
	fmt.Println("Сумма:", sum)
}
