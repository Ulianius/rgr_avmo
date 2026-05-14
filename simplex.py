from fractions import Fraction

original_n = 0
artificial_start = 0
artificial_vars = []
column_numbers = [] 
problem_type = "max" 

def read_problem(filename):
    global original_n, problem_type
    with open(filename, 'r') as f:
        lines = []
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)
    
    if lines and lines[-1].lower() in ["min", "max"]:
        problem_type = lines[-1].lower()
        lines = lines[:-1]
    else:
        problem_type = "max"
    
    all_rows = []
    for line in lines:
        parts = line.split()
        row = [Fraction(p) for p in parts]
        all_rows.append(row)
    
    Z = all_rows[-1]
    
    A = []
    b = []
    
    for i in range(len(all_rows) - 1):
        row = all_rows[i]
        coeffs = []
        for j in range(len(row) - 1):
            coeffs.append(row[j])
        A.append(coeffs)
        b.append(row[-1])
    
    if problem_type == "max":
        Z1 = [z * -1 for z in Z]
    else:
        Z1 = Z[:]
    
    original_n = len(Z1)
    return A, b, Z1

def normalize_rhs(A, b):
    for i in range(len(A)):
        if b[i] < 0:
            b[i] = -b[i]
            for j in range(len(A[i])):
                A[i][j] = -A[i][j]
    return A, b

def print_system(A, b, Z):
    n = len(Z)
    m = len(A)
    
    print("\n" + "="*50)
    print("Решение задачи линейного программирования методом искусственного базиса")
    print("="*50)
    print(f"\nПеременных: n = {n}")
    print(f"Ограничений: m = {m}")
    
    print("\nZ =", end=" ")
    for i in range(n):
        if Z[i] != 0:
            if i > 0 and Z[i] > 0:
                print("+", end=" ")
            print(f"{-Z[i]}·x{i+1}", end=" ")
    print("→ max")
    
    print("\nОграничения:")
    for i in range(m):
        for j in range(len(A[i])):
            if j > 0 and A[i][j] > 0:
                print("+", end=" ")
            print(f"{A[i][j]}·x{j+1}", end=" ")
        print(f"= {b[i]}")
    
    print("\nУсловия: x_i ≥ 0")

def normalize_z_row(A, b, Z, basis_to_row):
    new_Z = Z[:]
    
    for var_index, row_num in basis_to_row.items():
        if var_index < len(new_Z) - 1 and abs(new_Z[var_index]) > 1e-10:
            coeff = new_Z[var_index]
            
            for j in range(len(new_Z) - 1):
                if j < len(A[row_num]):
                    new_Z[j] -= coeff * A[row_num][j]
                    if abs(new_Z[j]) < 1e-10:
                        new_Z[j] = Fraction(0)
            
            new_Z[-1] -= coeff * b[row_num]
            if abs(new_Z[-1]) < 1e-10:
                new_Z[-1] = Fraction(0)
    
    return new_Z

def add_basis(A, b, Z):
    global artificial_start, artificial_vars, column_numbers
    i = 0
    while i < len(A):
        all_zero = True
        for j in range(len(A[i])):
            if A[i][j] != 0:
                all_zero = False
                break
        
        if all_zero:
            if b[i] != 0:
                print(f"\nОшибка: все коэффициенты в ограничении {i+1} равны 0!")
                print(f"   Уравнение: 0 = {b[i]}")
                print("   Это противоречие! Задача не имеет решений.")
                return None, None, None, None, None
            else:
                print(f"\nУдаляем нулевое ограничение {i+1}: 0 = 0")
                del A[i]
                del b[i]
                i -= 1
        i += 1
    
    m = len(A)
    if m == 0:
        print("\n Ошибка: все ограничения удалены!")
        return None, None, None, None, None
        
    n = 0
    for row in A:
        n = max(n, len(row))
    
    column_numbers = list(range(1, n + 1))
    
    new_A = []
    for i in range(m):
        row = A[i][:]
        while len(row) < n:
            row.append(Fraction(0))
        new_A.append(row)
    
    basis_rows = [-1] * m
    basis_to_row = {}
    
    for j in range(n):
        col = [new_A[i][j] for i in range(m)]
        one_i = -1
        is_basis = True
        
        for i in range(m):
            if col[i] == 1:
                if one_i == -1:
                    one_i = i
                else:
                    is_basis = False
                    break
            elif col[i] != 0:
                is_basis = False
                break
        
        if is_basis and one_i != -1 and basis_rows[one_i] == -1:
            basis_rows[one_i] = j
            basis_to_row[j] = one_i
    
    print(f"Найдено базисных столбцов: {len(basis_to_row)}")
    
    need_basis = [i for i in range(m) if basis_rows[i] == -1]
    
    if need_basis:
        print(f"\nДобавляем {len(need_basis)} искусственных переменных")
    
    artificial_start = n
    artificial_vars = []
    
    new_Z = Z[:-1] + [Fraction(0)] * len(need_basis) + [Z[-1]]
    
    for idx, row_num in enumerate(need_basis):
        new_var_index = artificial_start + idx
        
        for i in range(m):
            if i == row_num:
                new_A[i].append(Fraction(1))
            else:
                new_A[i].append(Fraction(0))
        
        column_numbers.append(n + idx + 1)
        basis_to_row[new_var_index] = row_num
        basis_rows[row_num] = new_var_index
        artificial_vars.append(new_var_index)
    
    new_Z = normalize_z_row(new_A, b, new_Z, basis_to_row)
    
    basis = [-1] * m
    for var_index, row_num in basis_to_row.items():
        basis[row_num] = var_index
    
    total_cols = len(new_A[0])
    M = [Fraction(0)] * (total_cols + 1)
    
    for art_var in artificial_vars:
        M[art_var] = Fraction(1)
    
    for row_num in need_basis:
        art_var = basis_rows[row_num]
        if M[art_var] != 0:
            coeff = M[art_var]
            for j in range(total_cols + 1):
                if j < total_cols:
                    M[j] -= coeff * new_A[row_num][j]
                else:
                    M[j] -= coeff * b[row_num]
    
    for i in range(len(M)):
        if abs(M[i]) < 1e-10:
            M[i] = Fraction(0)
    
    print(f"Базис: {[f'x{column_numbers[i]}' for i in basis]}")
    if artificial_vars:
        print(f"Искусственные переменные: {[f'x{column_numbers[i]}' for i in artificial_vars]}")
    
    return new_A, b[:], new_Z, basis, M

def delete_column(A, b, Z, M, basis, col_index):
    global artificial_vars, column_numbers
    
    col_num = column_numbers[col_index]
    print(f"  Удаляем столбец x{col_num}")
    
    del column_numbers[col_index]
    
    for i in range(len(A)):
        if col_index < len(A[i]):
            del A[i][col_index]
    
    if Z and col_index < len(Z) - 1:
        del Z[col_index]
    
    if M and col_index < len(M) - 1:
        del M[col_index]
    
    for i in range(len(basis)):
        if basis[i] > col_index:
            basis[i] -= 1
    
    new_artificial = []
    for var in artificial_vars:
        if var > col_index:
            new_artificial.append(var - 1)
        elif var < col_index:
            new_artificial.append(var)
    artificial_vars = new_artificial

def matrix_basis_M(A, b, M):
    global column_numbers
    
    if not M:
        return None, None
    
    row1 = -1
    min_neg = None
    
    for i in range(len(M) - 1):
        if M[i] < 0 and abs(M[i]) > 1e-10:
            if min_neg is None or M[i] < min_neg:
                min_neg = M[i]
                row1 = i
    
    if row1 == -1:
        if abs(M[-1]) > 1e-10:
            print("\n M-строка не содержит отрицательных коэффициентов ")
            print(" Задача не имеет допустимого решения (система несовместна).")
        else:
            print("\n M-строка обнулена!")
        return None, None
    
    print(f"\nРазрешающий столбец (M): x{column_numbers[row1]} = {M[row1]}")
    
    CO = []
    valid_rows = []
    
    for i in range(len(b)):
        if row1 < len(A[i]) and A[i][row1] > 0:
            a = b[i] / A[i][row1]
            CO.append(a)
            valid_rows.append(i)
            print(f"Строка {i+1}: {b[i]} / {A[i][row1]} = {a}")
    
    if not CO:
        print("\n Нет положительных элементов в разрешающем столбце")
        print("  Задача не имеет допустимого решения.")
        return None, None
    
    min_index = 0
    for i in range(len(CO)):
        if CO[i] < CO[min_index]:
            min_index = i
    
    row2 = valid_rows[min_index]
    print(f"Разрешающая строка: {row2+1}")
    
    return row1, row2

def matrix_basis_Z(A, b, Z):
    global column_numbers
    
    row1 = -1
    min_neg = None
    
    for i in range(len(Z) - 1):
        if Z[i] < 0 and abs(Z[i]) > 1e-10:
            if min_neg is None or Z[i] < min_neg:
                min_neg = Z[i]
                row1 = i
    
    if row1 == -1:
        return None, None
    
    print(f"\nРазрешающий столбец (Z): x{column_numbers[row1]} = {Z[row1]}")
    
    CO = []
    valid_rows = []
    
    for i in range(len(b)):
        if row1 < len(A[i]) and A[i][row1] > 0:
            a = b[i] / A[i][row1]
            CO.append(a)
            valid_rows.append(i)
            print(f"Строка {i+1}: {b[i]} / {A[i][row1]} = {a}")
    
    if not CO:
        return None, None
    
    min_index = 0
    for i in range(len(CO)):
        if CO[i] < CO[min_index]:
            min_index = i
    
    row2 = valid_rows[min_index]
    print(f"Разрешающая строка: {row2+1}")
    
    return row1, row2

def perform_simplex_step(A, b, Z, M, basis, row1, row2):
    pivot = A[row2][row1]
    
    for j in range(len(A[row2])):
        A[row2][j] /= pivot
    b[row2] /= pivot
    
    for i in range(len(A)):
        if i != row2:
            factor = A[i][row1]
            if factor != 0:
                for j in range(len(A[i])):
                    A[i][j] -= factor * A[row2][j]
                    if abs(A[i][j]) < 1e-10:
                        A[i][j] = Fraction(0)
                b[i] -= factor * b[row2]
                if abs(b[i]) < 1e-10:
                    b[i] = Fraction(0)
    
    if Z:
        factor_z = Z[row1]
        if factor_z != 0:
            for j in range(len(Z)):
                if j < len(A[row2]):
                    Z[j] -= factor_z * A[row2][j]
                    if abs(Z[j]) < 1e-10:
                        Z[j] = Fraction(0)
                elif j == len(A[row2]):
                    Z[j] -= factor_z * b[row2]
                    if abs(Z[j]) < 1e-10:
                        Z[j] = Fraction(0)
    
    if M:
        factor_m = M[row1]
        if factor_m != 0:
            for j in range(len(M)):
                if j < len(A[row2]):
                    M[j] -= factor_m * A[row2][j]
                    if abs(M[j]) < 1e-10:
                        M[j] = Fraction(0)
                elif j == len(A[row2]):
                    M[j] -= factor_m * b[row2]
                    if abs(M[j]) < 1e-10:
                        M[j] = Fraction(0)
    
    new_basis = basis[:]
    new_basis[row2] = row1
    
    return A, b, Z, M, new_basis

def simplex_iteration(A, b, Z, M, basis, row1, row2):
    global artificial_vars, column_numbers
    
    print(f"\n--- Итерация ---")
    print(f"Текущий базис: {[f'x{column_numbers[i]}' for i in basis]}")
    
    pivot = A[row2][row1]
    print(f"Разрешающий элемент: A[{row2+1}][{column_numbers[row1]}] = {pivot}")
    
    old_var = basis[row2]
    print(f"Переменная x{column_numbers[old_var]} выходит из базиса")
    
    is_artificial = old_var in artificial_vars
    if is_artificial:
        print(f"  (x{column_numbers[old_var]} - искусственная переменная)")
        print(f"\n Искусственная переменная x{column_numbers[old_var]} вышла из базиса")
        
        new_A, new_b, new_Z, M, new_basis = perform_simplex_step(A, b, Z, M, basis, row1, row2)
        delete_column(new_A, new_b, new_Z, M, new_basis, old_var)
        
        return new_A, new_b, new_Z, M, new_basis
    else:
        print(f"  (x{column_numbers[old_var]} - обычная переменная)")
        
        new_A, new_b, new_Z, M, new_basis = perform_simplex_step(A, b, Z, M, basis, row1, row2)
        return new_A, new_b, new_Z, M, new_basis

def check_M_zero(M):
    if not M:
        return True
    for i in range(len(M)):
        if abs(M[i]) > 1e-10:
            return False
    return True

def check_Z_positive(Z):
    for i in range(len(Z) - 1):
        if Z[i] < 0 and abs(Z[i]) > 1e-10:
            return False
    return True

def print_matrix(A, b, Z, M, basis):
    global column_numbers
    
    if not A or not A[0]:
        print("Матрица пуста")
        return
    
    n_cols = len(A[0])
    
    print("\n      ", end="")
    for j in range(n_cols):
        if j < len(column_numbers):
            val = column_numbers[j]
            print(f"  x{val:<3}", end="")
        else:
            print(f"  x?   ", end="")
    print("  св.чл.")
    print("    " + "-" * (n_cols * 8 + 8))
    
    for i in range(len(A)):
        if i < len(basis) and basis[i] >= 0 and basis[i] < len(column_numbers):
            val = column_numbers[basis[i]]
            print(f"x{val:<2}|", end="")
        else:
            print("   |", end="")
        
        for j in range(n_cols):
            val = A[i][j]
            if val.denominator == 1:
                print(f" {val.numerator:>4} ", end="")
            else:
                print(f" {val.numerator}/{val.denominator:<2}", end="")
        
        if b[i].denominator == 1:
            print(f"| {b[i].numerator:>4}")
        else:
            print(f"| {b[i].numerator}/{b[i].denominator}")
    
    print("    " + "-" * (n_cols * 8 + 8))
    
    if Z and len(Z) > 0:
        print(" Z |", end="")
        for j in range(n_cols):
            if j < len(Z) - 1:
                val = Z[j]
                if val.denominator == 1:
                    print(f" {val.numerator:>4} ", end="")
                else:
                    print(f" {val.numerator}/{val.denominator:<2}", end="")
            else:
                print(f" {0:>4} ", end="")
        
        if Z[-1].denominator == 1:
            print(f"| {Z[-1].numerator:>4}")
        else:
            print(f"| {Z[-1].numerator}/{Z[-1].denominator}")
    
    if M and len(M) > 0:
        print(" M |", end="")
        for j in range(n_cols):
            if j < len(M) - 1:
                val = M[j]
                if val.denominator == 1:
                    print(f" {val.numerator:>4} ", end="")
                else:
                    print(f" {val.numerator}/{val.denominator:<2}", end="")
            else:
                print(f" {0:>4} ", end="")
        
        if M[-1].denominator == 1:
            print(f"| {M[-1].numerator:>4}")
        else:
            print(f"| {M[-1].numerator}/{M[-1].denominator}")

def format_fraction(frac):
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"

def solve_simplex(A, b, Z):
    """Основная функция решения симплекс-методом"""
    global original_n, artificial_vars, column_numbers
    
    print_system(A, b, Z)
    
    result = add_basis(A, b, Z)
    if result[0] is None:
        return None
    
    new_A, new_b, new_Z, basis, M = result
    
    print("\n" + "="*50)
    print("НАЧАЛЬНАЯ МАТРИЦА С M-СТРОКОЙ")
    print("="*50)
    print_matrix(new_A, new_b, new_Z, M, basis)
    
    print("\n" + "="*60)
    print("ЭТАП 1: ОБНУЛЕНИЕ M СТРОКИ")
    print("="*60)
    
    iteration = 0
    max_iter = 100
    
    while not check_M_zero(M) and iteration < max_iter:
        iteration += 1
        print(f"\n--- Итерация {iteration} (обнуление M) ---")
        
        row1, row2 = matrix_basis_M(new_A, new_b, M)
        
        if row1 is None or row2 is None:
            if check_M_zero(M):
                print("\nM СТРОКА ОБНУЛИЛАСЬ!")
            else:
                return None
            break
        
        new_A, new_b, new_Z, M, basis = simplex_iteration(new_A, new_b, new_Z, M, basis, row1, row2)
        print_matrix(new_A, new_b, new_Z, M, basis)
    
    if iteration >= max_iter:
        print("\nДостигнуто максимальное количество итераций!")
        return None
    
    if artificial_vars:
        print("\nОстались искусственные переменные в базисе!")
        print("Задача не имеет допустимого решения.")
        return None
    
    M = []
    basis_to_row = {}
    for i in range(len(basis)):
        if basis[i] >= 0:
            basis_to_row[basis[i]] = i
    
    new_Z = normalize_z_row(new_A, new_b, new_Z, basis_to_row)
    
    print("\n" + "="*60)
    print("МАТРИЦА ПОСЛЕ УДАЛЕНИЯ M-СТРОКИ")
    print("="*60)
    print_matrix(new_A, new_b, new_Z, M, basis)
    
    print("\n" + "="*60)
    print("ЭТАП 2: ОПТИМИЗАЦИЯ Z СТРОКИ")
    print("="*60)
    
    iteration = 0
    
    while not check_Z_positive(new_Z) and iteration < max_iter:
        iteration += 1
        print(f"\n--- Итерация {iteration} (оптимизация Z) ---")
        
        row1, row2 = matrix_basis_Z(new_A, new_b, new_Z)
        
        if row1 is None or row2 is None:
            print("\nОптимальное решение найдено!")
            break
        
        new_A, new_b, new_Z, M, basis = simplex_iteration(new_A, new_b, new_Z, M, basis, row1, row2)
        print_matrix(new_A, new_b, new_Z, M, basis)
    
    print("\n" + "="*60)
    print("ФИНАЛЬНОЕ РЕШЕНИЕ")
    print("="*60)
    print_matrix(new_A, new_b, new_Z, M, basis)
    
    # Сохраняем текущее решение как первую точку (X1)
    X1 = []
    for i in range(len(column_numbers)):
        if i in basis:
            row = basis.index(i)
            X1.append(new_b[row])
        else:
            X1.append(Fraction(0))
    
    z_value = new_Z[-1]
    if problem_type == "max":
        final_z = -z_value
        print(f"\nМаксимальное значение Z = {final_z}")
    else:
        final_z = z_value
        print(f"\nМинимальное значение Z = {final_z}")
    
    non_basis_zero = []
    for i in range(len(new_Z) - 1):
        if i not in basis and new_Z[i] == 0:
            non_basis_zero.append(i)
    
    if non_basis_zero:
        # Находим переменную для ввода в базис (выбираем x1 если есть)
        free_var = None
        for var in non_basis_zero:
            if column_numbers[var] == 1:
                free_var = var
                break
        if free_var is None:
            free_var = non_basis_zero[0]
        
        # Делаем копию таблицы для нахождения второй точки
        temp_A = [row[:] for row in new_A]
        temp_b = new_b[:]
        temp_basis = basis[:]
        
        # Вводим свободную переменную в базис
        row1 = free_var
        row2 = -1
        min_ratio = None
        
        for i in range(len(temp_b)):
            if row1 < len(temp_A[i]) and temp_A[i][row1] > 0:
                ratio = temp_b[i] / temp_A[i][row1]
                if min_ratio is None or ratio < min_ratio:
                    min_ratio = ratio
                    row2 = i
        
        if row2 != -1:
            # Делаем шаг симплекс-метода
            pivot = temp_A[row2][row1]
            for j in range(len(temp_A[row2])):
                temp_A[row2][j] /= pivot
            temp_b[row2] /= pivot
            
            for i in range(len(temp_A)):
                if i != row2:
                    factor = temp_A[i][row1]
                    if factor != 0:
                        for j in range(len(temp_A[i])):
                            temp_A[i][j] -= factor * temp_A[row2][j]
                        temp_b[i] -= factor * temp_b[row2]
            
            temp_basis[row2] = row1
            
            # Получаем вторую точку (X2)
            X2 = []
            for i in range(len(column_numbers)):
                if i in temp_basis:
                    row = temp_basis.index(i)
                    X2.append(temp_b[row])
                else:
                    X2.append(Fraction(0))
            
            print("\n" + "="*60)
            print("МНОЖЕСТВО ОПТИМАЛЬНЫХ РЕШЕНИЙ")
            print("="*60)
            
            # Выводим X1 и X2
            print(f"\nX₁ = (", end="")
            for i in range(len(column_numbers)):
                print(f"x{i+1}={format_fraction(X1[i])}", end="")
                if i < len(column_numbers) - 1:
                    print(", ", end="")
            print(")")
            
            print(f"X₂ = (", end="")
            for i in range(len(column_numbers)):
                print(f"x{i+1}={format_fraction(X2[i])}", end="")
                if i < len(column_numbers) - 1:
                    print(", ", end="")
            print(")")
            
            print(f"\nZ = {final_z}")
            print("\nОбщее решение:")
            print(f"X(λ) = λ·X₂ + (1-λ)·X₁, где λ ∈ [0, 1]")
            
            # Выводим в развернутом виде
            print("\nВ развернутом виде:")
            expr_str = "X(λ) = ("
            for i in range(len(column_numbers)):
                val1 = X1[i]
                val2 = X2[i]
                if val1 == val2:
                    expr_str += f"x{i+1}={format_fraction(val1)}"
                elif val1 == 0 and val2 != 0:
                    expr_str += f"x{i+1}={format_fraction(val2)}·λ"
                elif val2 == 0 and val1 != 0:
                    expr_str += f"x{i+1}={format_fraction(val1)}·(1-λ)"
                else:
                    expr_str += f"x{i+1}={format_fraction(val1)}·(1-λ) + {format_fraction(val2)}·λ"
                if i < len(column_numbers) - 1:
                    expr_str += ", "
            expr_str += ")"
            print(expr_str)
            print("="*60)
        else:
            print("\n" + "="*60)
            print("ЕДИНСТВЕННОЕ РЕШЕНИЕ")
            print("="*60)
            X1_str = "X* = ("
            for i in range(len(column_numbers)):
                X1_str += f"x{i+1}={format_fraction(X1[i])}"
                if i < len(column_numbers) - 1:
                    X1_str += ", "
            X1_str += ")"
            print(f"\n{X1_str}")
            print(f"Z = {final_z}")
            print("="*60)
    
    else:
        print("\n" + "="*60)
        print("ЕДИНСТВЕННОЕ РЕШЕНИЕ")
        print("="*60)
        X1_str = "X* = ("
        for i in range(len(column_numbers)):
            X1_str += f"x{i+1}={format_fraction(X1[i])}"
            if i < len(column_numbers) - 1:
                X1_str += ", "
        X1_str += ")"
        print(f"\n{X1_str}")
        print(f"Z = {final_z}")
        print("="*60)
    
    return new_A, new_b, new_Z, basis

print("ЗАДАЧА 1")
print("="*70)
A, b, Z = read_problem("1.txt")
A, b = normalize_rhs(A, b)
solve_simplex(A, b, Z)