
import numpy as np
from hashlib import blake2b
import yaml
import json
from copy import deepcopy
import importlib
import inspect
import os


xopt_logo = """  _   
                | |  
__  _____  _ __ | |_ 
\ \/ / _ \| '_ \| __|
 >  < (_) | |_) | |_ 
/_/\_\___/| .__/ \__|
          | |        
          |_|        
"""



#--------------------------------
# Config utilities

def load_config(source, verbose=False):
    """
    Returns a dict loaded from a JSON or YAML file. 
    
    If source is already a dict, just returns the same dict.
    
    """    
    
    if not source:
        return source
    
    if isinstance(source, dict):
        return source
    
    if isinstance(source, str):
        file = full_path(source)
        assert os.path.exists(file), f'File does not exist: {file}'
        if source.endswith('json'):
            if verbose:
                print(f'Loading {file} as JSON ')
            return json.load(open(file))
        elif source.endswith('yaml'):
            if verbose:
                print(f'Loading {file} as YAML ')
            return yaml.safe_load(open(file))
    else:
        raise Exception(f'Do not know how to load {source}')
        
def save_config(data, filename, verbose=True):
    """
    Saves data to a JSON or YAML file, chosen by the filename extension.  
    
    """
    if filename.endswith('json'):
        with open(filename, 'w') as f:
            json.dump(data, f, ensure_ascii=True, indent='  ')
        if verbose:
            print(f'Config written as JSON to {filename}')
    elif filename.endswith('yaml'):
        with open(filename, 'w') as f:
            yaml.dump(data, f, default_flow_style=None, sort_keys=False)
        if verbose:
            print(f'Config written as YAML to {filename}')            
    else:
        raise



#--------------------------------
# VOCS utilities
def save_vocs(vocs_dict, filePath=None):
    """
    Write VOCS dictionary to a JSON file. 
    If no filePath is given, the name is chosen from the 'name' key + '.json'
    """

    if filePath:
        name = filePath
    else:
        name = vocs_dict['name']+'.json'
    with open(name, 'w') as outfile:
        json.dump(vocs_dict, outfile, ensure_ascii=True, indent='  ')
    print(name, 'written')
    
    
def load_vocs(filePath):
    """
    Load VOCS from a JSON file
    Returns a dict
    """
    with open(filePath, 'r') as f:
        dat = json.load(f)
    return dat    
    


def random_settings(vocs, include_constants=True, include_linked_variables=True):
    """
    Uniform sampling of the variables described in vocs['variables'] = min, max.
    Returns a dict of settings. 
    If include_constants, the vocs['constants'] are added to the dict. 
    
    """
    settings = {}
    for key, val in vocs['variables'].items():
        a, b = val
        x = np.random.random()
        settings[key] = x*a + (1-x)*b
        
    # Constants    
    if include_constants:
        settings.update(vocs['constants'])
        
    # Handle linked variables
    if include_linked_variables and 'linked_variables' in vocs and vocs['linked_variables']:
        for k, v in vocs['linked_variables'].items():
            settings[k] = settings[v]
        
    return settings    

def random_settings_arrays(vocs, n, include_constants=True, include_linked_variables=True):
    """
    Similar to random_settings, but with arrays of size n. 
    
    Uniform sampling of the variables described in vocs['variables'] = min, max.
    Returns a dict of settings, with each settings as an array. 

    If include_constants, the vocs['constants'] are added to the dict as full arrays.
    
    """
    settings = {}
    for key, val in vocs['variables'].items():
        a, b = val
        x = np.random.random(n)
        settings[key] = x*a + (1-x)*b
        
    # Constants    
    if include_constants:
        for k, v in vocs['constants'].items():
            settings[k] = np.full(n, v)
        
    # Handle linked variables
    if include_linked_variables and 'linked_variables' in vocs and vocs['linked_variables']:
        for k, v in vocs['linked_variables'].items():
            settings[k] = np.full(n, settings[v])
        
    return settings    




#--------------------------------
# Vector encoding and decoding
    
# Decode vector to dict
def decode1(vec, labels):
    return dict(zip(labels, vec.tolist()))
# encode dict to vector
def encode1(d, labels):
    return [d[key] for key in labels]    
    

#--------------------------------
# Paths
    
def full_path(path, ensure_exists=True):
    """
    Makes path abolute. Can ensure exists. 
    """
    p = os.path.expandvars(path)
    p = os.path.abspath(p)
    if ensure_exists:
        assert os.path.exists(p), 'path does not exist: '+p
    return p

def add_to_path(path, prepend=True):
    """
    Add path to $PATH
    """
    p = full_path(path)
    
    if prepend:
        os.environ['PATH']  = p+os.pathsep+os.environ['PATH']
    else:
        # just append
        os.environ['PATH']  += os.pathsep+p
    return p    
    
def expand_paths(nested_dict, suffixes=['_file', '_path', '_bin'], verbose=True, sep='::', ensure_exists=False):
    """
    Crawls through a nested dict and expands the path of any key that ends 
    with characters in the suffixes list. 

    Internally flattens, and unflattens a dict to this using a seperator string sep
    
    """
    d = flatten_dict(nested_dict, sep=sep)
    
    for k, v in d.items():
        k2 = k.split(sep)
        if len(k2) == 1:
            k2 = k2[0]
        else:
            k2 = k2[-1]
        
        if any([k2.endswith(x) for x in suffixes]):
            if not v:
                if verbose:
                    print(f'Warning: No path set for key {k}')        
                continue
            file = full_path(v, ensure_exists=ensure_exists)
            if os.path.exists(file):
                d[k] = file
            else:
                if verbose:
                    print(f'Warning: Path {v} does not exist for key {k}')    
    
    return unflatten_dict(d, sep=sep)


#--------------------------------
# h5 utils

def write_attrs(h5, group_name, data):
    """
    Simple function to write dict data to attribues in a group with name
    """
    g = h5.create_group(group_name)
    for key in data:
        g.attrs[key] = data[key]
    return g



def write_attrs_nested(h5, name, data):
    """
    Recursive routine to write nested dicts to attributes in a group with name 'name'
    """
    if type(data) == dict:
        g = h5.create_group(name)
        for k, v in data.items():
            write_attrs_nested(g, k, v)
    else:
        h5.attrs[name] = data    
        
        
#--------------------------------
# data fingerprinting   
class NumpyEncoder(json.JSONEncoder):
    """
    See: https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
    """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
def fingerprint(keyed_data, digest_size=16):
    """
    Creates a cryptographic fingerprint from keyed data. 
    Used JSON dumps to form strings, and the blake2b algorithm to hash.
    
    """
    h = blake2b(digest_size=16)
    for key in keyed_data:
        val = keyed_data[key]
        s = json.dumps(val, sort_keys=True, cls=NumpyEncoder).encode()
        h.update(s)
    return h.hexdigest()          



#--------------------------------
# nested dict flattening, unflattening

def flatten_dict(dd, sep=':', prefix=''):
    """
    Flattens a nested dict into a single dict, with keys concatenated with sep.
    
    Similar to pandas.io.json.json_normalize
    
    Example:
        A dict of dicts:
            dd = {'a':{'x':1}, 'b':{'d':{'y':3}}}
            flatten_dict(dd, prefix='Z')
        Returns: {'Z:a:x': 1, 'Z:b:d:y': 3}
    
    """
    return { prefix + sep + k if prefix else k : v
             for kk, vv in dd.items()
             for k, v in flatten_dict(vv, sep, kk).items()
             } if isinstance(dd, dict) else { prefix : dd }

def unflatten_dict(d, sep=':', prefix=''):
    """
    Inverse of flatten_dict. Forms a nested dict.
    """
    dd = {}
    for kk, vv in d.items():
        if kk.startswith(prefix+sep):
            kk=kk[len(prefix+sep):]
            
        klist = kk.split(sep)
        d1 = dd
        for k in klist[0:-1]:
            if k not in d1:
                d1[k] = {}
            d1 = d1[k]
        
        d1[klist[-1]] = vv
    return dd

def update_nested_dict(d, settings, verbose=False):
    """
    Updates a nested dict with flattened settings
    """
    flat_params = flatten_dict(d)

    for key, value in settings.items():
        if verbose:
            if key in flat_params:
                print(f'Replacing param {key} with value {value}')
            else:
                print(f'New param {key} with value {value}')
        flat_params[key] = value
        
    new_dict = unflatten_dict(flat_params)
    
    return new_dict



#--------------------------------
# adding defaults to dicts
def fill_defaults(dict1, defaults, strict=True):
    """
    Fills a dict with defaults in a defaults dict. 
    
    dict1 must only contain keys in defaults.
    
    deepcopy is necessary!
    
    """
    # start with defaults
    for k in dict1:
        if k not in defaults and strict:
            raise Exception(f'Extraneous key: {k}. Allowable keys: '+', '.join(list(defaults)))
    for k, v in defaults.items():
        if k not in dict1:
            dict1[k] =  deepcopy(v)
            
            
            
#--------------------------------        
# Function manipulation


def get_function(name):
    """
    Returns a function from a fully qualified name or global name.
    """
    if name in globals(): 
        if callable(globals()[name]):
            f = globals()[name]
        else:
            raise ValueError(f'global {name} is not callable')
    else:
        # try to import
        m_name, f_name = name.rsplit('.', 1)
        module = importlib.import_module(m_name)
        f = getattr(module, f_name)
    
    return f           

def get_function_defaults(f):
    """
    Returns a dict of the non-empty POSITIONAL_OR_KEYWORD arguments.
    
    See the `inspect` documentation for detauls.
    """
    defaults = {}
    for k, v in inspect.signature(f).parameters.items():
        if v.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            #print(k, v.default, v.kind)
            if v.default != inspect.Parameter.empty:
                defaults[k] = v.default
    return defaults



def get_n_required_fuction_arguments(f):
    """
    Counts the number of required function arguments using the `inspect` module.
    """
    n = 0
    for k, v in inspect.signature(f).parameters.items():
        if v.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            if v.default == inspect.Parameter.empty:
                n += 1
    return n