from info.modules.index import index_blu


@index_blu.route('/')
def index():
    return '<h1>index-text</h1>'