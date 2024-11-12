from collections import namedtuple

# TODOL
import traceback

try:
    print('src/__init__.py: trying to import "run_universal", __name__ is "{__name__}"'.format(__name__=__name__))
    from src import run_universal as entry_point
    # if __name__ == '__main__':
    #     # run as a program
    #     from src import run_universal as entry_point
    #     #import run_universal as entry_point
    # if __name__ == 'mdmtoolsap_bundle':
    #     # first call within a bundle
    #     from src import run_universal as entry_point
    # elif '.' in __name__:
    #     # package
    #     from . import run_universal as entry_point
    # else:
    #     # included with no parent package
    #     import run_universal as entry_point
    # entry_point_main = entry_point.main
except ImportError as e:
    print('src/__init__.py: failed to import run_universal')
    print('src/__init__.py: traceback:')
    traceback.print_exception(e)
    print('src/__init__.py: end of traceback:')
    def entry_point_main():
        print('test: within src/__init__.py')


Run_universal = namedtuple('run_universal',['main'])
run_universal = Run_universal(entry_point_main)
