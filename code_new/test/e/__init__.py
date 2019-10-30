def _find_data_path():
    import os.path
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir, os.path.pardir, 'data'))


data_path = _find_data_path()