def pytest_addoption(parser):
    parser.addoption('--attempt', choices=('without', 'with'), default='without',
                     help='Select the isolated skill comparison implementation.')
