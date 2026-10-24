// Задание 10. Статистика последовательности.
package main

import (
	"bufio"
	"fmt"
	"math"
	"os"
	"strconv"
	"strings"
)

var reader = bufio.NewReader(os.Stdin)

func readInt(prompt string, min int) int {
	for {
		fmt.Print(prompt)
		line, err := reader.ReadString('\n')
		if err != nil && line == "" {
			fmt.Println("\nВвод завершён.")
			os.Exit(1)
		}
		v, err := strconv.Atoi(strings.TrimSpace(line))
		if err == nil && v >= min {
			return v
		}
		if err != nil {
			fmt.Println("Ошибка: введите целое число.")
		} else {
			fmt.Printf("Ошибка: число должно быть не меньше %d.\n", min)
		}
	}
}

// Stats — итоговые показатели.
type Stats struct {
	Sum     int
	Average float64
	Max     int
	Min     int
	Even    int
	Odd     int
}

// calcStats считает статистику по непустому срезу.
func calcStats(nums []int) Stats {
	s := Stats{Max: nums[0], Min: nums[0]}
	for _, x := range nums {
		s.Sum += x
		if x > s.Max {
			s.Max = x
		}
		if x < s.Min {
			s.Min = x
		}
		if x%2 == 0 {
			s.Even++
		} else {
			s.Odd++
		}
	}
	s.Average = float64(s.Sum) / float64(len(nums))
	return s
}

func main() {
	n := readInt("Сколько чисел будет введено? N = ", 1)
	nums := make([]int, 0, n)
	for i := 1; i <= n; i++ {
		nums = append(nums, readInt(fmt.Sprintf("Число %d: ", i), math.MinInt))
	}

	s := calcStats(nums)
	fmt.Println()
	fmt.Println("Статистика последовательности:")
	fmt.Println("Сумма:", s.Sum)
	fmt.Printf("Среднее значение: %.2f\n", s.Average)
	fmt.Println("Максимальное значение:", s.Max)
	fmt.Println("Минимальное значение:", s.Min)
	fmt.Println("Количество чётных чисел:", s.Even)
	fmt.Println("Количество нечётных чисел:", s.Odd)
}
