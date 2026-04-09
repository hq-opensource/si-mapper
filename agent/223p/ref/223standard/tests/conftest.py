import glob


def pytest_generate_tests(metafunc):
    if "data_file" in metafunc.fixturenames:
        args = glob.glob("../data/*.ttl")
        metafunc.parametrize("data_file", args)
