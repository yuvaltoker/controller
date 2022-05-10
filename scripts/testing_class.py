from dataclasses import dataclass, field

@dataclass
class Person:
    name: str = field(default='samyon', init=True)

def main():
    person = Person(name='yuval')
    print(person.name)
    person.name = 'dan'
    print(person.name)

if __name__ == '__main__':
    main()