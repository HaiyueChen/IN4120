def _find_data_path():
    import os.path
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.pardir, os.path.pardir, 'data'))


data_path = _find_data_path()


def run_all_tests():
    import inspect
    import unittest
    import os.path
    stack = inspect.stack()[1]
    file_path = stack[1]
    test_path = os.path.dirname(os.path.abspath(file_path))
    runner = unittest.TextTestRunner()
    suite = unittest.TestLoader().discover(test_path)
    runner.run(suite)


def simple_repl(prompt, evaluator):
    from timeit import default_timer as timer
    import pprint
    printer = pprint.PrettyPrinter()
    escape = "!"
    print(f"Enter '{escape}' to exit.")
    while True:
        query = input(f"{prompt}>")
        if query == escape:
            break
        start = timer()
        matches = evaluator(query)
        end = timer()
        printer.pprint(matches)
        print(f"Evaluation took {end - start} seconds.")
