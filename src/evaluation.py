"""
Business Entity Resolution - Evaluation Module
Implements the official competition metric: Macro F_0.5 score with strict singleton handling.
"""

from typing import Dict, Set, List, Tuple
import numpy as np

def compute_f05_score(precision: float, recall: float) -> float:
    """Computes F_0.5 score from precision and recall."""
    denom = 0.25 * precision + recall
    if denom <= 0.0:
        return 0.0
    return (1.25 * precision * recall) / denom

def evaluate_macro_f05(
    predictions: Dict[str, Set[str]],
    ground_truth: Dict[str, Set[str]]
) -> Dict[str, float]:
    """
    Computes macro-averaged F_0.5 score across all Source 1 entities in ground_truth.
    
    Singleton logic:
      - If true matches == 0 and predicted matches == 0: score = 1.0
      - If true matches == 0 and predicted matches > 0: score = 0.0
      - If true matches > 0 and predicted matches == 0: score = 0.0
      - If true matches > 0 and predicted matches > 0: score = F_0.5(P, R)
    """
    scores = []
    tp_total = 0
    fp_total = 0
    fn_total = 0
    
    singletons_correct = 0
    singletons_total = 0
    
    for s1_id, true_set in ground_truth.items():
        pred_set = predictions.get(s1_id, set())
        
        # Singleton handling
        if len(true_set) == 0:
            singletons_total += 1
            if len(pred_set) == 0:
                scores.append(1.0)
                singletons_correct += 1
            else:
                scores.append(0.0)
                fp_total += len(pred_set)
            continue
            
        if len(pred_set) == 0:
            scores.append(0.0)
            fn_total += len(true_set)
            continue
            
        tp = len(pred_set & true_set)
        fp = len(pred_set - true_set)
        fn = len(true_set - pred_set)
        
        tp_total += tp
        fp_total += fp
        fn_total += fn
        
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        scores.append(compute_f05_score(p, r))
        
    macro_f05 = float(np.mean(scores)) if scores else 0.0
    global_p = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0.0
    global_r = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0.0
    sing_acc = singletons_correct / singletons_total if singletons_total > 0 else 1.0
    
    return {
        'macro_f05': macro_f05,
        'precision': global_p,
        'recall': global_r,
        'tp': tp_total,
        'fp': fp_total,
        'fn': fn_total,
        'singleton_accuracy': sing_acc,
        'singletons_evaluated': singletons_total
    }
