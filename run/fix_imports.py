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
        
        # Import distutils.util specifically
        try:
            import setuptools._distutils.util as distutils_util
            sys.modules['distutils.util'] = distutils_util
        except ImportError:
            # Create a minimal util module if not available
            class DistutilsUtil:
                @staticmethod
                def strtobool(val):
                    """Convert a string representation of truth to true (1) or false (0)."""
                    val = val.lower()
                    if val in ('y', 'yes', 't', 'true', 'on', '1'):
                        return 1
                    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
                        return 0
                    else:
                        raise ValueError("invalid truth value %r" % (val,))
            
            sys.modules['distutils.util'] = DistutilsUtil()
    except ImportError:
        pass