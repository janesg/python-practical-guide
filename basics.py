
print('10 > 8 : ' + str(10 > 8))
print('10 < 8 : ' + str(10 < 8))
print('15 / 10 : ' + str(15 / 10))
print('15 // 10 : ' + str(15 // 10))
print('2 ** 3 : ' + str(2 ** 3))
print('16 % 5 : ' + str(16 % 5))
print('\'Bye \' * 5 : ' + 'Bye ' * 5)
print('"Bye " * 5 : ' + "Bye " * 5)

long_line = """A longer line 
      spanning multiple lines"""
print(long_line)

my_list = ['some text', 12.9, True, 27, ["I'm nested", False]]
print(my_list)
print('Length = ' + str(len(my_list)))
print(my_list[3])
print(my_list[4][0])
my_list[4][0] = "I'm nested and updated"
print(my_list)
my_list.insert(1, ['Inserted Text'])
my_list.pop(4)
my_list.append('***')
print(my_list)

def print_it(it):
    print(it)

print_it('It works')
