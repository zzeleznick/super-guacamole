# jsonly.py
#
# Author: Zach Zeleznick
# Pythonic Wrapper around a JSON-style dictionary and a generic testing suite

from collections import deque, namedtuple

Result = namedtuple("Result", ["status", "value"])
global tests
tests = []

def testsuite(func):
    """Testing Suite that counts number tests passed.
    Sadly, the suite cannot prevent against poorly written tests"""
    pad = lambda n: "-" * n
    run_mesage = "%s Test Suite Manager Begin %s" % (pad(3), pad(3))
    print(run_mesage)
    def inner(*args, **kwargs):
        res = func(*args, **kwargs)
        try:
            suiteExists = isinstance(tests, list)
        except NameError:
            pass
        else:
            correct = sum(tests)
            print("RESULT: Passed %s of %s tests" % (correct, len(tests)))
            end_mesage = "%s Test Suite Manager End %s" % (pad(3), pad(3))
            print(end_mesage)
        return res
    return inner

def testcase(func, printResult = True):
    """Calls a function that should return a Result Container in which
    the status and value are stored"""
    suiteExists = False
    try:
        suiteExists = isinstance(tests, list)
    except NameError:
        pass
    else:
        pass #print("Global test suite found")
    def wrapper(*args, **kwargs):
        name = func.__name__
        pad = lambda n: "-" * n
        run_mesage = "%s Running test %s %s" % (pad(6), name, pad(6))
        print(run_mesage)
        res = func(*args, **kwargs)
        if not isinstance(res, Result):
            raise(TypeError("Input function must return a Result Instance"))
        status, value = res.status, res.value
        if not isinstance(status, bool):
            print("WARNING: status should be either a bool [True or False]")
        if status is True or status:
            print("Test passes.")
        else:
            print("FAILURE: Test fails.")
        if printResult:
             print("Received value: %s" % (value))
        print("%s" % (pad(len(run_mesage))))
        if suiteExists:
            tests.append(status)
        return res
    return wrapper

class JSONWrapper(object):
    """An advanced wrapper around a JSON-style dictionary
    NOTE: fields must not contain a '.' as this is a special char"""
    # class member variables
    badInputError = TypeError("Must use strings for get")
    badTypeError = TypeError("Tried to key-reference a string")
    missingInputError = TypeError("No input received")
    missingKeyError = TypeError("No key found with that name")

    def __init__(self, dct):
        """Initialize with a dictonary as the only arg"""
        self.dct = dct

    def value(self):
        return self.dct

    @staticmethod
    def handle_failure(res, key):
        def _raise(x):
            raise(x)
        options = {0: lambda x: print(x),
                   1: lambda x: _raise(x),
                  }
        if key not in options:
            key = 1
        options[key](res)

    def get(self, name, failureOption = 1):
        """Retrieves a value or dictionary from a qualified field
        NOTE: fields must not contain a '.' as this is a special char"""
        if type(name) != str:
            self.handle_failure(self.badInputError, failureOption)
        if name is None:
            self.handle_failure(self.missingInputError, failureOption)
        fieldArray = name.split(".")
        cur = self.dct
        for field in fieldArray:
            if type(cur) != dict:
                self.handle_failure(self.badTypeError, failureOption)
            elif field not in cur:
                 self.handle_failure(self.missingKeyError, failureOption)
            else:
                cur = cur[field]

        return cur

    def getLeaves(self, getValues = True):
        """Retrieves the names and optional data of the deepest fields"""
        rootTuples = [(name,node) for name, node in self.dct.items()]
        queue = deque(rootTuples)
        result = []
        while queue:
            (name, node) = queue.popleft()
            if type(node) == dict:
                 for next_name, next_node in node.items():
                    queue.append( ("%s.%s" % (name,next_name), next_node) )
            else:
                if getValues:
                    result.append((name, node))
                else:
                    result.append(name)
        return result

    def to_dict(self):
        return self.dct

    def __repr__(self):
        return "%s" % self.dct

    def __getattr__(self, name):
        """Overrides the dot notation to allow for chained field calls"""
        try:
            result = JSONWrapper(self.dct[name])
        except Exception as e:
            raise(e)
        else:
            return result
@testcase
def check_get(obj, key, expectedValue):
    """Simple get and compare against expected"""
    print("Getting key '%s'" % key)
    value = obj.get(key)
    status = value == expectedValue
    res = Result(status, value)
    return res

@testcase
def check_dot_get(obj, keys, expectedValue):
    """Get via dot notiation and compare against expected"""
    if isinstance(keys, str):
        raise(TypeError("Keys should be an array of strings"))
    chained_keys = ".".join(keys)
    cmd = "obj." + chained_keys if chained_keys else "obj"
    cmd += ".value()"
    print("Running command '%s'" % cmd)
    value = eval(cmd)
    status = value == expectedValue
    res = Result(status, value)
    return res

@testcase
def check_leaves(obj, expectedValue):
    """Checks leaves call, order invariant"""
    value = obj.getLeaves()
    status = set(value) == set(expectedValue)
    res = Result(status, value)
    return res

@testsuite
def run_tests():
    myDict = {'localhost': {
                    'port': 4000, 'alias': "default",
                    "dict": { "foo": 12, "bar": "baz"},
                        },
             'other_host': {
                    'port': 80, 'alias': "server"},
             'owner': "zach",
        }
    obj = JSONWrapper(myDict)
    check_get(obj, "owner", "zach")
    check_dot_get(obj, ["owner"], "zach")
    check_get(obj, "other_host.port", 80)
    check_dot_get(obj, ["other_host", "port"], 80)
    check_get(obj, "localhost.dict.bar", "baz")
    expected_leaf_tuples = [('owner', 'zach'), ('other_host.port', 80), ('other_host.alias', 'server'),
                            ('localhost.port', 4000), ('localhost.alias', 'default'),
                            ('localhost.dict.foo', 12), ('localhost.dict.bar', 'baz')]
    check_leaves(obj, expected_leaf_tuples)

if __name__ == '__main__':

    run_tests()

    """
    print(obj.getLeaves())
    print(obj.get("owner"))
    print(obj.owner)
    print(obj.other_host)
    print(obj.other_host.port)
    print(obj.get("other_host.port"))
    print(obj.get("other_host")["port"])
    """