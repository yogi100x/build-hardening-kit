package dal

import "testing"

func TestListUsersStartsEmpty(t *testing.T) {
	if got := len(ListUsers()); got != 0 {
		t.Fatalf("got %d users, want 0", got)
	}
}
