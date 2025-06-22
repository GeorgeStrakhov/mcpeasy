"""
Advanced Calculator tool implementation - evaluates mathematical expressions with support for 
trigonometric functions, logarithms, constants, and more
"""

import ast
import math
import operator
from typing import Any, Dict, Optional
from src.tools.base import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """Advanced calculator tool for evaluating mathematical expressions with functions and constants"""
    
    # Define safe operations for the calculator
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.BitXor: operator.pow,  # Treat ^ as exponentiation (standard mathematical notation)
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Mod: operator.mod,
    }
    

    
    # Define safe mathematical functions following standard mathematical notation
    SAFE_FUNCTIONS = {
        # Trigonometric functions
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'sec': lambda x: 1 / math.cos(x),    # secant
        'csc': lambda x: 1 / math.sin(x),    # cosecant
        'cot': lambda x: 1 / math.tan(x),    # cotangent
        
        # Inverse trigonometric functions
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'atan2': math.atan2,
        'arcsin': math.asin,    # Alternative notation
        'arccos': math.acos,    # Alternative notation
        'arctan': math.atan,    # Alternative notation
        
        # Hyperbolic functions
        'sinh': math.sinh,
        'cosh': math.cosh,
        'tanh': math.tanh,
        'sech': lambda x: 1 / math.cosh(x),  # hyperbolic secant
        'csch': lambda x: 1 / math.sinh(x),  # hyperbolic cosecant
        'coth': lambda x: 1 / math.tanh(x),  # hyperbolic cotangent
        
        # Inverse hyperbolic functions
        'asinh': math.asinh,
        'acosh': math.acosh,
        'atanh': math.atanh,
        'arcsinh': math.asinh,  # Alternative notation
        'arccosh': math.acosh,  # Alternative notation
        'arctanh': math.atanh,  # Alternative notation
        
        # Logarithmic and exponential functions (standard notation)
        'ln': math.log,         # Natural logarithm (standard notation)
        'log': math.log10,      # Common logarithm (base 10, standard in many contexts)
        'log10': math.log10,    # Explicit base-10 logarithm
        'log2': math.log2,      # Base-2 logarithm
        'lg': math.log2,        # Base-2 logarithm (alternative notation)
        'logb': lambda x, b: math.log(x) / math.log(b),  # Logarithm with arbitrary base
        'exp': math.exp,        # e^x
        'exp2': lambda x: 2 ** x,  # 2^x
        'exp10': lambda x: 10 ** x,  # 10^x
        'expm1': math.expm1,    # exp(x) - 1
        'log1p': math.log1p,    # ln(1 + x)
        
        # Power and root functions
        'sqrt': math.sqrt,      # Square root
        'cbrt': lambda x: math.copysign(abs(x) ** (1/3), x),  # Cube root (handles negative numbers)
        'root': lambda x, n: math.copysign(abs(x) ** (1/n), x) if n % 2 == 1 else abs(x) ** (1/n),  # nth root
        'pow': math.pow,        # Power function
        'square': lambda x: x ** 2,  # Square function
        'cube': lambda x: x ** 3,    # Cube function
        
        # Rounding and absolute functions
        'abs': abs,
        'ceil': math.ceil,
        'floor': math.floor,
        'round': round,
        'trunc': math.trunc,
        'sign': lambda x: math.copysign(1, x),  # Sign function
        
        # Combinatorics and number theory
        'factorial': math.factorial,
        'perm': math.perm,      # Permutations
        'comb': math.comb,      # Combinations (binomial coefficients)
        'gcd': math.gcd,        # Greatest common divisor
        'lcm': math.lcm,        # Least common multiple
        
        # Angular conversions
        'degrees': math.degrees,
        'radians': math.radians,
        'deg': math.degrees,    # Short form
        'rad': math.radians,    # Short form
        
        # Special functions
        'gamma': math.gamma,    # Gamma function
        'lgamma': math.lgamma,  # Log gamma function
        'erf': math.erf,        # Error function
        'erfc': math.erfc,      # Complementary error function
        
        # Utility functions
        'min': min,
        'max': max,
        'sum': sum,
        'mean': lambda *args: sum(args) / len(args),  # Arithmetic mean
        'mod': lambda x, y: x % y,  # Modulo (alternative to % operator)
    }
    
    # Define mathematical constants following standard notation
    SAFE_CONSTANTS = {
        'pi': math.pi,          # π ≈ 3.14159
        'e': math.e,            # Euler's number ≈ 2.71828
        'tau': math.tau,        # τ = 2π ≈ 6.28318
        'phi': (1 + math.sqrt(5)) / 2,  # Golden ratio ≈ 1.61803
        'inf': math.inf,        # Infinity
        'nan': math.nan,        # Not a number
        
        # Alternative notation
        'π': math.pi,           # Unicode pi
        'euler': math.e,        # Alternative name for e
        'golden': (1 + math.sqrt(5)) / 2,  # Alternative name for golden ratio
        'infinity': math.inf,   # Alternative name for infinity
    }
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return ("Advanced mathematical calculator following standard mathematical notation. "
                "Supports trigonometric, logarithmic, exponential functions, and mathematical constants. "
                "Examples: sin(π/2), ln(e), log(100), sqrt(16), comb(5,2)")
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": ("Mathematical expression using standard notation. Supports: "
                                  "• Arithmetic: +, -, *, /, %, ** (or ^) for exponentiation "
                                  "• Trigonometric: sin, cos, tan, sec, csc, cot (and arc- variants) "
                                  "• Logarithmic: ln (natural), log (base-10), log2, lg "
                                  "• Exponential: exp, exp2, exp10 "
                                  "• Constants: pi/π, e/euler, tau, phi/golden "
                                  "• Examples: 'sin(π/4)', 'ln(e)', 'log(100)', 'e^2', 'comb(5,2)'")
                }
            },
            "required": ["expression"]
        }
    
    def _safe_eval(self, node):
        """Safely evaluate mathematical expressions using AST (Python 3.12+)"""
        if isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            # Handle constants like pi, e, tau
            if node.id in self.SAFE_CONSTANTS:
                return self.SAFE_CONSTANTS[node.id]
            else:
                raise ValueError(f"Unknown identifier: {node.id}")
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            op = self.SAFE_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            op = self.SAFE_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operation: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Call):
            # Handle function calls like sin(x), log(x), etc.
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are supported")
            
            func_name = node.func.id
            if func_name not in self.SAFE_FUNCTIONS:
                raise ValueError(f"Unknown function: {func_name}")
            
            func = self.SAFE_FUNCTIONS[func_name]
            args = [self._safe_eval(arg) for arg in node.args]
            
            # Handle keyword arguments if any
            if node.keywords:
                raise ValueError("Keyword arguments are not supported")
            
            try:
                return func(*args)
            except (ValueError, TypeError, OverflowError) as e:
                raise ValueError(f"Error in function {func_name}: {str(e)}")
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")

    async def execute(self, arguments: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute the calculator tool"""
        expression = arguments.get("expression", "").strip()
        
        if not expression:
            return ToolResult.error("No expression provided")
        
        try:
            # Parse the expression into an AST
            tree = ast.parse(expression, mode='eval')
            
            # Evaluate the expression safely
            result = self._safe_eval(tree)
            
            # Format the result nicely
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            
            # Return structured JSON data
            calculation_data = {
                "expression": expression,
                "result": result,
                "result_type": type(result).__name__,
                "formatted_output": f"{expression} = {result}"
            }
            
            return ToolResult.json(calculation_data)
            
        except ZeroDivisionError:
            return ToolResult.error("Division by zero error")
        except ValueError as e:
            return ToolResult.error(f"Invalid expression: {str(e)}")
        except SyntaxError:
            return ToolResult.error("Invalid mathematical expression syntax")
        except OverflowError:
            return ToolResult.error("Mathematical overflow - result too large")
        except Exception as e:
            return ToolResult.error(f"Error evaluating expression: {str(e)}")