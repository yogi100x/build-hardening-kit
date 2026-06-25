//go:build ruleguard

// Custom AST lint rules via go-ruleguard, hosted by gocritic (see .golangci.yml).
// This is the Go analog of the custom ESLint plugin: project-specific footguns,
// matched on the syntax tree, blocked at lint time.
package gorules

import "github.com/quasilyte/go-ruleguard/dsl"

// Forbid raw DB queries outside the dal/ package — mirror of no-raw-db-client.
func rawDBQuery(m dsl.Matcher) {
	m.Match(
		`$db.Query($*_)`,
		`$db.QueryContext($*_)`,
		`$db.Exec($*_)`,
		`$db.ExecContext($*_)`,
	).
		Where(!m.File().PkgPath.Matches(`.*/dal(/.*)?$`)).
		Report(`raw DB query outside dal/ — move it into a DAL function`)
}

// Example: ban fmt.Println in committed code (use a logger).
func noFmtPrintln(m dsl.Matcher) {
	m.Match(`fmt.Println($*_)`).
		Report(`use the structured logger, not fmt.Println`)
}
