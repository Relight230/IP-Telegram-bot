def sum_of_nums():
    N = int(input("Введите число(N), до которого хотьите посчитать сумму: "))
    arr = [el for el in range(N)]
    print(arr)
    print("Сумма чисел до N: ", sum(arr))

sum_of_nums()