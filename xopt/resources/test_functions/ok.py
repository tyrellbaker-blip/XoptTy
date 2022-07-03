from xopt import VOCS

ok_vocs_yaml = """
variables:
    x1: [0, 10]
    x2: [0, 10]
    x3: [1, 5]
    x4: [0, 6]
    x5: [1, 5]
    x6: [0, 10] 
objectives:
    f1: MINIMIZE
    f2: MINIMIZE
constraints:
    g1: [GREATER_THAN, 0]
    g2: [GREATER_THAN, 0]
    g3: [GREATER_THAN, 0]
    g4: [GREATER_THAN, 0]
    g5: [GREATER_THAN, 0]
    g6: [GREATER_THAN, 0]
"""

ok_vocs = VOCS.from_yaml(ok_vocs_yaml)

def evaluate_ok(inputs):
    
    """  
    Osyczka Kundu (OK) function
    https://en.wikipedia.org/wiki/Test_functions_for_optimization#cite_note-OsyczkaKundu1995-22
    
    Osyczka, Andrzej and Sourav Kundu. "A new method to solve generalized multicriteria optimization problems using the simple genetic algorithm."" Structural optimization 10 (1995): 94-99.
    
    variables:
        x1: [0, 10]
        x2: [0, 10]
        x3: [1, 5]
        x4: [0, 6]
        x5: [1, 5]
        x6: [0, 10] 
    objectives:
        f1: MINIMIZE
        f2: MINIMIZE
    constraints:
        g1: [GREATER_THAN, 0]
        g2: [GREATER_THAN, 0]
        g3: [GREATER_THAN, 0]
        g4: [GREATER_THAN, 0]
        g5: [GREATER_THAN, 0]
        g6: [GREATER_THAN, 0]
    """
    
    x1 = inputs["x1"]
    x2 = inputs["x2"]
    x3 = inputs["x3"]
    x4 = inputs["x4"]
    x5 = inputs["x5"]
    x6 = inputs["x6"]
        
    outputs = {
        "f1": -25*(x1-2)**2 - (x2-2)**2 - (x3-1)**2 - (x4-4)**2 - (x5-1)**2,
        "f2": x1**2 + x2**2 + x3**2 + x4**2 + x5**2 + x6**2,
        "g1": x1 + x2 - 2,
        "g2": 6 - x1 - x2,
        "g3": 2 - x2 + x1,
        "g4": 2 - x1 + 3*x2,
        "g5": 4 - (x3-3)**2 - x4,
        "g6": (x5-3)**2 + x6 - 4
    }
    
    return outputs
     
    