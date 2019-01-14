from os.path import join


def base_template(template_name):
    templates_dir = 'templates'

    with open(join(templates_dir, f'{template_name}.html')) as template:
        return template.read()


def index():
    return base_template('index')


def blog():
    return base_template('blog')
