# 1) Create a list of “person” dictionaries with a name, age and list of hobbies for each person. Fill in any data you want.
# 2) Use a list comprehension to convert this list of persons into a list of names (of the persons).
# 3) Use a list comprehension to check whether all persons are older than 20.
# 4) Copy the person list such that you can safely edit the name of the first person (without changing the original list).
# 5) Unpack the persons of the original list into different variables and output these variables.

people = [
    {'name': 'John', 'age': 27, 'hobbies': ['Golf', 'Cycling']},
    {'name': 'Enid', 'age': 18, 'hobbies': ['Lip Plumping', 'Selfies']}
]

names = [person['name'] for person in people]
print('Names: {}'.format(names))

everyone_older_than_20 = all(person['age'] > 20 for person in people)
print('Everyone older than 20 ? : {}'.format(everyone_older_than_20))

people_snapshot = [person.copy() for person in people]
people_snapshot[0]['name'] = 'Rufus'
print('Original People: {}'.format(people))
print('Snapshot People: {}'.format(people_snapshot))

person1, person2 = people
print('Person 1: {}'.format(person1))
print('Person 2: {}'.format(person2))

