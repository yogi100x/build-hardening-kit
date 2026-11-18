package main

import (
	"fmt"

	"example.com/fixture/dal"
)

func main() {
	fmt.Printf("%d users\n", len(dal.ListUsers()))
}
