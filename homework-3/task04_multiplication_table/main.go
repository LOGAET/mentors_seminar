// Задание 4. Таблица умножения через функцию.
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

// printTable выводит n x 1 ... n x 10.
func printTable(n int) {
	fmt.Printf("Таблица умножения для %d:\n", n)
	for i := 1; i <= 10; i++ {
		fmt.Printf("%d x %2d = %d\n", n, i, n*i)
	}
}

func main() {
	reader := bufio.NewReader(os.Stdin)
	for {
		fmt.Print("Введите число: ")
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
		printTable(n)
		return
	}
}
