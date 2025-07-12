"""
Compatibility shim for Python 3.12+ that provides missing modules
"""
import sys
import importlib.util
import importlib

# Fix for missing 'imp' module in Python 3.12+
if 'imp' not in sys.modules or not hasattr(sys.modules.get('imp', None), 'load_module'):
    class ImpCompat:
        @staticmethod
        def load_source(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        
        @staticmethod
        def find_module(name):
            try:
                spec = importlib.util.find_spec(name)
                if spec:
                    return (None, spec.origin, ('', '', spec.loader))
                else:
                    raise ImportError(f"No module named '{name}'")
            except ImportError:
                raise ImportError(f"No module named '{name}'")
        
        @staticmethod 
        def load_module(name, file, pathname, description):
            try:
                return importlib.import_module(name)
            except ImportError:
                spec = importlib.util.spec_from_file_location(name, pathname)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
    
    sys.modules['imp'] = ImpCompat()

# Fix for missing 'distutils' module  
if 'distutils' not in sys.modules:
    try:
        import setuptools._distutils as distutils
        sys.modules['distutils'] = distutils
        sys.modules['distutils.util'] = distutils.util
    except ImportError:
        pass