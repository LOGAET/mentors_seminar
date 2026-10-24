// Задание 8. Проверка простого числа.
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

// isPrime проверяет делители до √n.
func isPrime(n int) bool {
	if n < 2 {
		return false
	}
	if n == 2 {
		return true
	}
	if n%2 == 0 {
		return false
	}
	for d := 3; d <= n/d; d += 2 {
		if n%d == 0 {
			return false
		}
	}
	return true
}

func main() {
	reader := bufio.NewReader(os.Stdin)
	for {
		fmt.Print("Введите целое число: ")
		line, err := reader.ReadString('\n')
		if err != nil && line == "" {
			fmt.Println("\nВвод завершён.")
			return
		}
		n, err := strconv.Atoi(strings.TrimSpace(line))
		if err != nil {
			fmt.Println("Ошибка: введите целое число.")
			continue
		}
		if isPrime(n) {
			fmt.Printf("%d — простое число.\n", n)
		} else {
			fmt.Printf("%d — не является простым числом.\n", n)
		}
		return
	}
}
