def generator_init(func):
    def inner(*args, **kwargs):
        init_gen = func(*args, **kwargs)
        init_gen.send(None)
        return init_gen

    return inner


@generator_init
def average():
    count = 0
    summary = 0
    inner_average = None

    while True:
        try:
            x = yield inner_average
        except StopIteration:
            print('done!')
            break
        else:
            count += 1
            summary += x if x is not None else 1
            inner_average = round(summary / count, 2)

    return inner_average


def gen(string):
    for letter in string:
        yield letter


all_things = ''
g = gen('say something!')
for i in g:
    all_things += i
    print(all_things)
