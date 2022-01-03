# 1) Create a list of names and use a for loop to output the length of each name (len() ).
# 2) Add an if  check inside the loop to only output names longer than 5 characters.
# 3) Add another if  check to see whether a name includes a “n”  or “N”  character.
# 4) Use a while  loop to empty the list of names (via pop() )

names = ['Bob', 'Fanny', 'Joseph', 'Enid']
print('Length of names list is: {}'.format(len(names)))

for name in names:
    if len(name) > 5:
        print('Name: {}, is {} characters in length'.format(name, len(name)))

    if 'n' in name or 'N' in name:
        print('Name: {}, contains "n" or "N" character'.format(name))

while len(names) > 0:
    print('Names: {}'.format(names))
    names.pop()
else:
    print('Names: {}'.format(names))
