def output_name_age(name, age):
    print(name + ' : ' + str(age))


def output_any(arg1, arg2):
    print(str(arg1) + ' : ' + str(arg2))


def decades(age):
    return int(age / 10)


name = input('Enter your name : ')
age = input('Enter your age : ')

output_name_age(name, age)
output_any(['Bob', 23.12, [1,2,3]], False)
print("If your age is 56, you've been alive for " + str(decades(56)) + ' decade(s)')

