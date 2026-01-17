import math

# Function to perform addition
def add(x, y):
    return x + y

# Function to perform subtraction
def subtract(x, y):
    return x - y

# Function to perform multiplication
def multiply(x, y):
    return x * y

# Function to perform division
def divide(x, y):
    if y == 0:
        return 'Error! Division by zero.'
    return x / y

# Function to perform square root
def sqrt(x):
    return math.sqrt(x)

# Function to perform exponentiation
def power(x, y):
    return x ** y

# Main function to run the calculator
def scientific_calculator():
    print('Scientific Calculator')
    print('1. Add')
    print('2. Subtract')
    print('3. Multiply')
    print('4. Divide')
    print('5. Square Root')
    print('6. Exponentiation')
    choice = input('Enter your choice (1-6): ')
    if choice in ['1', '2', '3', '4', '6']:
        num1 = float(input('Enter first number: '))
        num2 = float(input('Enter second number: '))
    elif choice == '5':
        num1 = float(input('Enter number: '))
    else:
        print('Invalid choice')
        return
    if choice == '1':
        print(f'Result: {add(num1, num2)}')
    elif choice == '2':
        print(f'Result: {subtract(num1, num2)}')
    elif choice == '3':
        print(f'Result: {multiply(num1, num2)}')
    elif choice == '4':
        print(f'Result: {divide(num1, num2)}')
    elif choice == '5':
        print(f'Result: {sqrt(num1)}')
    elif choice == '6':
        print(f'Result: {power(num1, num2)}')

if __name__ == '__main__':
    scientific_calculator()