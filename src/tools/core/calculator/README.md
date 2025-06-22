# Calculator Tool

Advanced mathematical calculator supporting arithmetic operations, trigonometric functions, logarithms, exponentials, and mathematical constants following standard mathematical notation.

## Purpose
Evaluate complex mathematical expressions with support for functions, constants, and advanced mathematical operations using standard mathematical notation.

## Parameters

| Parameter  | Type   | Required | Description                                                    |
|------------|--------|----------|----------------------------------------------------------------|
| expression | string | Yes      | Mathematical expression to evaluate (e.g., "sin(π/4)", "log(100)", "e^2") |

## Configuration
No configuration required.

## Features
- **Standard Mathematical Notation**: Uses `ln` for natural log, `log` for base-10, `^` for exponentiation
- **Trigonometric Functions**: `sin`, `cos`, `tan`, `sec`, `csc`, `cot` (and arc- variants)
- **Hyperbolic Functions**: `sinh`, `cosh`, `tanh`, `sech`, `csch`, `coth`
- **Logarithmic Functions**: `ln` (natural), `log` (base-10), `log2`, `lg`, `logb`
- **Exponential Functions**: `exp`, `exp2`, `exp10`
- **Mathematical Constants**: `pi`/`π`, `e`/`euler`, `tau`, `phi`/`golden`
- **Power & Root Functions**: `sqrt`, `cbrt`, `root`, `square`, `cube`
- **Combinatorics**: `factorial`, `perm`, `comb`, `gcd`, `lcm`
- **Special Functions**: `gamma`, `erf`, `erfc`, `abs`, `sign`
- **Utility Functions**: `min`, `max`, `sum`, `mean`, `mod`
- **Safe Evaluation**: Uses AST parsing to prevent code injection

## Supported Operations

### Arithmetic
- `+`, `-`, `*`, `/`, `%` (modulo)
- `**` or `^` (exponentiation)

### Trigonometric
- `sin(x)`, `cos(x)`, `tan(x)`
- `sec(x)`, `csc(x)`, `cot(x)`
- `asin(x)`, `acos(x)`, `atan(x)` (or `arcsin`, `arccos`, `arctan`)

### Logarithmic & Exponential
- `ln(x)` - Natural logarithm
- `log(x)` - Base-10 logarithm
- `log2(x)` - Base-2 logarithm
- `logb(x, base)` - Arbitrary base logarithm
- `exp(x)` - e^x
- `exp2(x)` - 2^x

### Constants
- `pi` or `π` ≈ 3.14159
- `e` or `euler` ≈ 2.71828
- `tau` ≈ 6.28318
- `phi` or `golden` ≈ 1.61803

## Example Usage

**Basic Arithmetic:**
```json
{
  "expression": "2 + 3 * 4"
}
```

**Trigonometric:**
```json
{
  "expression": "sin(π/2) + cos(0)"
}
```

**Complex Expression:**
```json
{
  "expression": "sqrt(16) + ln(e^2) - log(100) + factorial(4)"
}
```

**Using Exponentiation:**
```json
{
  "expression": "2^3 * e^1 + 10^2"
}
```

## Output Format

The tool returns structured JSON with:

```json
{
  "expression": "sin(π/6) + cos(π/3)",
  "result": 1.0,
  "result_type": "float",
  "formatted_output": "sin(π/6) + cos(π/3) = 1.0"
}
```

## Error Handling
- **Division by Zero**: Returns specific error for division by zero
- **Invalid Syntax**: Handles malformed mathematical expressions
- **Unsupported Operations**: Clear error messages for unsupported functions
- **Mathematical Errors**: Catches domain errors (e.g., `sqrt(-1)`, `log(-1)`)
- **Overflow Protection**: Handles extremely large numbers gracefully

## Mathematical Notation Notes
- Uses standard mathematical notation: `ln` for natural log, `log` for base-10
- Supports both `**` and `^` for exponentiation
- Handles negative numbers correctly in root functions (e.g., `cbrt(-8) = -2`)
- Unicode constants supported (e.g., `π` in addition to `pi`) 