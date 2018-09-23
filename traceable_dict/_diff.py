from _utils import key_added, key_removed, key_updated, root

__all__ = []


class DictDiff(object):
    """
    Deep nested difference of dicts, identifying added, removed and changed keys.
    
    Note: a basic assumption of this class is that dictionary describes a schema. Meaning:

        1. all values are found in the leafs.

        2. if a value of a leaf changes from non-dict to dict, this is a scheme change.
           Which is not supported here.

    Example:

        >>> from traceable_dict import DictDiff
        >>>
        >>> d1 = {'old_key': 'old_value'}
        >>> d2 = d1.copy()
        >>> d2['new_key'] = 'new_val'
        >>>
        >>> DictDiff.find_diff(d1, d2)
        [(('_root_', 'new_key'), None, __added__)]

    """
   
    @staticmethod
    def find_diff(t1, t2, path=[root]):
        """
        Find deep nested difference in dicts.
        
        Params:
        -------
        t1 : dict,
            Original dictionary.
        t2: dict,
            Other dictionary, to compare to.

        Returns:
        -------
        updates: list,
            List of updates that happened while in the transition from t1 to t2.
        """
        t1_keys = set(t1.keys())
        t2_keys = set(t2.keys())
        
        t_keys_intersect = t2_keys.intersection(t1_keys)
        
        t_keys_added = t2_keys - t_keys_intersect
        t_keys_removed = t1_keys - t_keys_intersect
        
        updates = []
        for k in t_keys_intersect:
            
            curr_path = path[:]
            curr_path.append(k)
            
            if (not isinstance(t1[k], dict)) and (not isinstance(t2[k], dict)):
                if (t1[k] != t2[k]):
                    updates.append((tuple(curr_path), t1[k], key_updated))
            else:
                updates.extend(DictDiff.find_diff(t1[k], t2[k], curr_path))

        for k in t_keys_added:
            for leaf_path, val in DictDiff._traversal(t2[k]):
                updates.append((tuple(path + [k] + leaf_path), None, key_added))

        for k in t_keys_removed:
            for leaf_path, val in DictDiff._traversal(t1[k]):
                updates.append((tuple(path + [k] + leaf_path), val, key_removed))

        return updates

    @staticmethod
    def _traversal(t):
        """
        Performs tree traversal over all leafs in the tree.
        
        Params:
        -------
        t : dict,
            Input dictionary.

        Returns:
        -------
        leafs: list,
            List of tuples describing the leafs in the tree
            Leaf tuple is of format (value, path_to_leaf).
        """
        leafs = []
        stack = []
        stack.append((t, []))
        while stack:
            node, path = stack.pop()
            if not isinstance(node, dict):
                leafs.append((path, node))
                continue
            for k in node.keys():
                curr_path = path[:]
                curr_path.append(k)
                stack.append((node[k], curr_path))
        return leafs

    
__all__ += ['DictDiff']
