from __future__ import unicode_literals

import collections
import copy
import functools
import json
import sys

try:
    from collections.abc import Sequence
except ImportError:  # Python 3
    from collections import Sequence

try:
    from types import MappingProxyType
except ImportError:
    # Python < 3.3
    MappingProxyType = dict

from jsonpointer import JsonPointer, JsonPointerException


_ST_ADD = 0
_ST_REMOVE = 1


try:
    from collections.abc import MutableMapping, MutableSequence

except ImportError:
    from collections import MutableMapping, MutableSequence
    str = unicode

# Will be parsed by setup.py to determine package metadata
__author__ = 'Stefan Kögl <stefan@skoegl.net>'
__version__ = '1.33'
__website__ = 'https://github.com/stefankoegl/python-json-patch'
__license__ = 'Modified BSD License'


# pylint: disable=E0611,W0404
if sys.version_info >= (3, 0):
    basestring = (bytes, str)  # pylint: disable=C0103,W0622


class JsonPatchException(Exception):
    """Base Json Patch exception"""


class InvalidJsonPatch(JsonPatchException):
    """ Raised if an invalid JSON Patch is created """


class JsonPatchConflict(JsonPatchException):
    """Raised if patch could not be applied due to conflict situation such as:
    - attempt to add object key when it already exists;
    - attempt to operate with nonexistence object key;
    - attempt to insert value to array at position beyond its size;
    - etc.
    """


class JsonPatchTestFailed(JsonPatchException, AssertionError):
    """ A Test operation failed """


def multidict(ordered_pairs):
    # read all values into lists
    """
    Creates a dictionary by unpacking lists into individual values. It takes an
    iterable of ordered pairs and returns a dictionary with each key mapping to a
    list of its corresponding values.

    Args:
        ordered_pairs (iterable.): 2D list of key-value pairs that are read into
            the `mdict` dictionary, with each key-value pair as an item in the list.
            
            		- `ordered_pairs`: This is a sequence of tuples, where each tuple
            contains two elements - the key and its corresponding value.
            		- `len(values)`: This is the number of values associated with each
            key in the input. If there is only one value associated with a given
            key, then `len(values)` returns 1.
            		- `defaultdict(list)`: This is the default dictionary returned by
            the `collections` module's `defaultdict` function when passed an empty
            argument list. In this case, the default dictionary has `key` as the
            keys and `list` as the values.
            
            	Therefore, the `multidict` function returns a dictionary with the
            key-value pairs from `ordered_pairs`, where each key has a list of
            corresponding values if there are multiple values associated with it
            in `ordered_pairs`.

    Returns:
        dict: a dictionary where each key maps to a list of corresponding values.

    """
    mdict = collections.defaultdict(list)
    for key, value in ordered_pairs:
        mdict[key].append(value)

    return dict(
        # unpack lists that have only 1 item
        (key, values[0] if len(values) == 1 else values)
        for key, values in mdict.items()
    )


# The "object_pairs_hook" parameter is used to handle duplicate keys when
# loading a JSON object.
_jsonloads = functools.partial(json.loads, object_pairs_hook=multidict)


def apply_patch(doc, patch, in_place=False, pointer_cls=JsonPointer):
    """
    Takes a `document` and a `patch` parameter and applies the patch to the document.

    Args:
        doc (dict): documentation to be updated or modified by the `patch` input
            parameter.
        patch (str): patch that will be applied to the `doc` object.
        in_place (bool): Whether to apply changes directly to the document instead
            of creating a new version.
        pointer_cls (int): class used to convert JSON Pointers into instances of
            the `pointer_cls` class during the apply operation.

    Returns:
        JsonPatch: a `JsonPointer` object representing the modified document.
        
        	1/ The `patch` argument: This is the patch that is applied to the input
        `doc`. It can be either a string representing a JSON Patch document or an
        instance of `JsonPatch`.
        	2/ The `in_place` argument: If set to `True`, the patch is applied directly
        to the input `doc`, modifying its original content. Otherwise, a new copy
        of the modified document is returned.
        	3/ The `pointer_cls` argument: This is the class used to create pointer
        objects that represent the elements in the input `doc`. It can be any class
        derived from `JsonPointer`.

    """
    if isinstance(patch, basestring):
        patch = JsonPatch.from_string(patch, pointer_cls=pointer_cls)
    else:
        patch = JsonPatch(patch, pointer_cls=pointer_cls)
    return patch.apply(doc, in_place)


def make_patch(src, dst, pointer_cls=JsonPointer):
    return JsonPatch.from_diff(src, dst, pointer_cls=pointer_cls)


class PatchOperation(object):

    def __init__(self, operation, pointer_cls=JsonPointer):
        """
        Initializes a `JsonPointer` object, which assigns the operation's `path`
        member to a `self.location` attribute and a `pointer` attribute either
        derived from the `path` member or explicitly passed as an instance of `JsonPointer`.

        Args:
            operation (object or instance of the class `Operation`.): JSON patch
                operation that contains a `path` member, which is used to determine
                the location of the pointer and the actual value being operated on.
                
                	1/ `operation`: This is the input object that contains the
                properties and attributes of the JSON patch operation.
                	2/ `'path'`: This is a required member of the operation object,
                indicating the path to the resource being updated. If this member
                is missing, an error will be raised.
                	3/ `pointer_cls`: This is an optional class parameter that specifies
                the type of pointer to use for the path. If it is not provided,
                it defaults to `JsonPointer`.
                	4/ `location`: This is the location of the resource being updated,
                which can either be a direct path or a pointer to the resource.
                If the `path` member is a pointer, then `location` will be set to
                the pointer value. Otherwise, it will be set to the direct path value.
                	5/ `pointer`: This is an optional attribute that stores the actual
                pointer value if the `path` member is also a pointer. It can be a
                `JsonPointer` object or any other type of pointer. If it is not
                provided, it will be initialized using the `pointer_cls` parameter.
            pointer_cls (int): Python class used to store the location information
                of an item that has been updated or created.

        """
        self.pointer_cls = pointer_cls

        if not operation.__contains__('path'):
            raise InvalidJsonPatch("Operation must have a 'path' member")

        if isinstance(operation['path'], self.pointer_cls):
            self.location = operation['path'].path
            self.pointer = operation['path']
        else:
            self.location = operation['path']
            try:
                self.pointer = self.pointer_cls(self.location)
            except TypeError as ex:
                raise InvalidJsonPatch("Invalid 'path'")

        self.operation = operation

    def apply(self, obj):
        raise NotImplementedError('should implement the patch operation.')

    def __hash__(self):
        return hash(frozenset(self.operation.items()))

    def __eq__(self, other):
        """
        Determines if two `PatchOperation` objects are equal by comparing their
        `operation` attributes.

        Args:
            other (instance of PatchOperation): 2nd patch operation that is being
                compared with the current instance of `PatchOperation`.
                
                		- If it is not an instance of `PatchOperation`, then the method
                returns `False`.
                		- Otherwise, the method checks if the `operation` attribute of
                `self` is equal to the `operation` attribute of `other`. If they
                are equal, the method returns `True`.

        Returns:
            bool: a boolean value indicating whether the input `other` instance
            is also an instance of `PatchOperation`.

        """
        if not isinstance(other, PatchOperation):
            return False
        return self.operation == other.operation

    def __ne__(self, other):
        return not(self == other)

    @property
    def path(self):
        return '/'.join(self.pointer.parts[:-1])

    @property
    def key(self):
        """
        Takes a `Pointer` object as input and returns either an integer value or
        the last part of the pointer string.

        Returns:
            int: an integer representing the value of the last item in a given pointer.

        """
        try:
            return int(self.pointer.parts[-1])
        except ValueError:
            return self.pointer.parts[-1]

    @key.setter
    def key(self, value):
        """
        Updates the `location` attribute of an object's `operation` dictionary
        with a new path value derived from the last element of its own `pointer.path`.

        Args:
            value (str): value that is assigned to the last part of the `Pointer`
                object's path during the function call.

        """
        self.pointer.parts[-1] = str(value)
        self.location = self.pointer.path
        self.operation['path'] = self.location


class RemoveOperation(PatchOperation):

    def apply(self, obj):
        """
        Modifies an object by removing an element at a specified position, using
        a pointer to navigate the object's hierarchy.

        Args:
            obj (`object`.): object that contains the part to be removed.
                
                		- `subobj`: The original object after applying the `to_last`
                method to extract the last sub-object from the sequence or mapping.
                		- `part`: The index or key of the property to remove in the `subobj`.
                
                	When raising an exception, the function checks for both `KeyError`
                and `IndexError` to provide a more detailed error message when
                trying to remove a non-existent object.

        Returns:
            instance of the `obj` passed as input to the function, without any
            modifications made to it: a modified version of the input `obj`.
            
            		- `obj`: The object on which the function is called.
            		- `subobj`: The sub-object to which the function applies.
            		- `part`: The part or index of the sub-object that corresponds to
            the key in the JSON patch.
            
            	The function returns the original `obj` unchanged if any error occurs
            during the removal of the key, including `KeyError` and `IndexError`.
            Additionally, if the key is not present in the `subobj`, a `JsonPatchConflict`
            exception is raised with a custom message.

        """
        subobj, part = self.pointer.to_last(obj)

        if isinstance(subobj, Sequence) and not isinstance(part, int):
            raise JsonPointerException("invalid array index '{0}'".format(part))

        try:
            del subobj[part]
        except (KeyError, IndexError) as ex:
            msg = "can't remove a non-existent object '{0}'".format(part)
            raise JsonPatchConflict(msg)

        return obj

    def _on_undo_remove(self, path, key):
        """
        Updates a internal key based on undo/redo operations performed on the
        provided path and key. The key is increased or decreased based on the
        relative position of the provided key within the internal array.

        Args:
            path (str): directory or file path to which the `key` parameter refers.
            key (int): 16-bit undo history index for the given path, and incrementing
                or decrementing it updates the corresponding entry in the undo stack.

        Returns:
            int: the next key value in the undo stack.

        """
        if self.path == path:
            if self.key >= key:
                self.key += 1
            else:
                key -= 1
        return key

    def _on_undo_add(self, path, key):
        """
        Updates the value of a key in a list when the path matches the current
        path and the key is greater than or equal to the current key, otherwise
        it decrements the key by 1.

        Args:
            path (str): tree path of the node to which the undo event occurred.
            key (int): 2nd most recent change in the undo stack, and it is decremented
                when the function is called if its value is greater than or equal
                to the value of the `self.key`.

        Returns:
            int: the smaller of two integer values.

        """
        if self.path == path:
            if self.key > key:
                self.key -= 1
            else:
                key -= 1
        return key


class AddOperation(PatchOperation):

    def apply(self, obj):
        """
        Applies a JSON patch to an object by resolving the Pointer location and
        performing the appropriate operation based on the Part of the pointer.

        Args:
            obj (`object`.): document that is being modified based on the JSON
                patch applied using the function.
                
                		- `obj`: The JSON document to be modified, which can be either
                an object or a list.
                		- `pointer`: A `Pointer` object that contains information about
                the location of the JSON pointer in the document.
                		- `operation`: An `Operation` object that represents the update
                operation to be applied to the JSON document. It includes information
                about the operation's value and the member it should be applied
                to in the document.
                
                	The function first attempts to extract the value of the operation
                from the `value` member of the `operation` object, using the
                `try`-`except` block to handle any errors that may occur. If the
                extraction is successful, the function then checks the type of the
                subobject (i.e., the part of the document where the operation
                should be applied) and performs the appropriate modification based
                on the type. The returned value is the original `obj` document,
                which may have been modified during the application of the operation.

        Returns:
            instance of the original input `obj: the modified object based on the
            given JSON patch operation.
            
            		- `obj`: The input object that was passed to the function for modification.
            		- `value`: The value that is being applied to the input object.
            		- `subobj`: A subobject of the input object that corresponds to the
            part of the JSON pointer. This can be a list or a dictionary.
            		- `part`: The specific part of the JSON pointer that corresponds to
            the subobject.
            
            	In summary, the `apply` function modifies an input object by applying
            a value to a specified part of its structure, based on a JSON pointer.
            The returned output is the modified input object.

        """
        try:
            value = self.operation["value"]
        except KeyError as ex:
            raise InvalidJsonPatch(
                "The operation does not contain a 'value' member")

        subobj, part = self.pointer.to_last(obj)

        if isinstance(subobj, MutableSequence):
            if part == '-':
                subobj.append(value)  # pylint: disable=E1103

            elif part > len(subobj) or part < 0:
                raise JsonPatchConflict("can't insert outside of list")

            else:
                subobj.insert(part, value)  # pylint: disable=E1103

        elif isinstance(subobj, MutableMapping):
            if part is None:
                obj = value  # we're replacing the root
            else:
                subobj[part] = value

        else:
            if part is None:
                raise TypeError("invalid document type {0}".format(type(subobj)))
            else:
                raise JsonPatchConflict("unable to fully resolve json pointer {0}, part {1}".format(self.location, part))
        return obj

    def _on_undo_remove(self, path, key):
        """
        Updates the key value based on the relative position of the element within
        a undo stack, increasing the key by 1 if the element is at the same path
        as the current stack top and the element's key is greater than the current
        stack top, or adding 1 to the key of the element if it is not at the same
        path.

        Args:
            path (str): path of the file or folder being undone.
            key (int): 2nd position element of the tuple used to store and manage
                the undo history.

        Returns:
            int: the updated value of `key`.

        """
        if self.path == path:
            if self.key > key:
                self.key += 1
            else:
                key += 1
        return key

    def _on_undo_add(self, path, key):
        """
        Updates a variable `key` based on the difference between the passed `path`
        and the instance's own `path`. The update is performed by adjusting `key`
        by the amount equal to the difference between the two paths.

        Args:
            path (str): current undo path being worked on, which is used to determine
                the position of the key to be adjusted in the undo buffer.
            key (int): 1-based index of the next element to be undone after the
                current element in the given path.

        Returns:
            int: the new value of `key`.

        """
        if self.path == path:
            if self.key > key:
                self.key -= 1
            else:
                key += 1
        return key


class ReplaceOperation(PatchOperation):

    def apply(self, obj):
        """
        Applies a JSON patch operation to an object by following a pointer provided
        by a JSON Pointer syntax. It checks the type of the sub-object, validates
        the part of the pointer, and replaces the value of the sub-object with the
        one specified in the patch operation.

        Args:
            obj (object (of any subclass).): JSON document that is being updated
                through the application of the patch operation.
                
                		- `obj`: The JSON patch operation object.
                		- `self`: The instance of the `JsonPatchOperation` class.
                		- `operation`: A dictionary containing the operation details.
                		- `pointer`: An instance of the `Pointer` class, representing
                the json pointer for the operation.
                		- `to_last`: A method of the `Pointer` class, used to convert a
                json pointer to a last-level dictionary key.
                		- `isinstance`: A Python built-in function used to check if an
                object is an instance of a specific class.
                		- `MutableSequence`: An abbreviation for a mutable sequence,
                which can be modified after creation.
                		- `MutibleMapping`: An abbreviation for a mutable mapping, which
                can be modified after creation.
                		- `type`: A Python built-in function used to determine the type
                of an object.
                
                	In the function body, various checks and modifications are made
                on `obj` depending on its properties:
                
                		- If `part` is `None`, an exception is raised due to an invalid
                document type.
                		- If `part >= len(subobj)` or `part < 0`, an exception is raised
                because `part` is outside of the list.
                		- If `isinstance(subobj, MutableSequence) and part not in subobj`,
                an exception is raised because the object cannot be replaced outside
                of a list.
                		- If `isinstance(subobj, MutableMapping)` and `part` is not in
                the mapping, an exception is raised because the object cannot be
                replaced for a non-existent key.
                		- Otherwise, if `part is None`, an exception is raised due to
                an invalid json pointer.
                
                	In summary, `obj` is deserialized and analyzed for various
                properties and attributes before undergoing modification in
                accordance with the operation specified in the dictionary.

        Returns:
            object: a modified version of the original object with the specified
            change applied to the correct location.
            
            		- `subobj`: The subtree part of the object that was applied to, which
            can be a nested dictionary or list.
            		- `part`: The key part of the json pointer that led to this subtree.
            		- `value`: The value that was applied to the subtree at `part`.
            
            	The function checks if the given object can be successfully applied
            with the specified operation. If it is not possible, it raises a
            `InvalidJsonPatch` exception with a specific message related to the problem.
            
            	In the returned output, `subobj`, `part`, and `value` provide information
            about the part of the object that was modified or updated by the
            function. The `subobj` and `part` attributes give the details of the
            subtree that was operated on, while `value` represents the value that
            was applied to that subtree.

        """
        try:
            value = self.operation["value"]
        except KeyError as ex:
            raise InvalidJsonPatch(
                "The operation does not contain a 'value' member")

        subobj, part = self.pointer.to_last(obj)

        if part is None:
            return value

        if part == "-":
            raise InvalidJsonPatch("'path' with '-' can't be applied to 'replace' operation")

        if isinstance(subobj, MutableSequence):
            if part >= len(subobj) or part < 0:
                raise JsonPatchConflict("can't replace outside of list")

        elif isinstance(subobj, MutableMapping):
            if part not in subobj:
                msg = "can't replace a non-existent object '{0}'".format(part)
                raise JsonPatchConflict(msg)
        else:
            if part is None:
                raise TypeError("invalid document type {0}".format(type(subobj)))
            else:
                raise JsonPatchConflict("unable to fully resolve json pointer {0}, part {1}".format(self.location, part))

        subobj[part] = value
        return obj

    def _on_undo_remove(self, path, key):
        return key

    def _on_undo_add(self, path, key):
        return key


class MoveOperation(PatchOperation):

    def apply(self, obj):
        """
        Performs a JSON patch operation on an object, updating it based on information
        contained within a `operation` dictionary. The function retrieves the
        relevant values from the object and the operation, then applies the necessary
        modifications to produce a new version of the object.

        Args:
            obj (`object`.): Python object that will be updated with the patch operation.
                
                		- `obj`: The input object that will be patched.
                		- `operation`: A `json_patch.JsonPatch` instance representing a
                set of patch operations to apply to the input object.
                		- `from_ptr`: A pointer object representing the starting point
                of the patch operation, which can be either an instance of the
                `self.pointer_cls` class or a direct string representation.
                		- `part`: The part of the input object that the patch operation
                applies to, which can be either a string or a numerical index.
                		- `subobj`: A mutable object (such as a dictionary or list) that
                contains the target of the patch operation.
                		- `value`: The value that will be added or removed from the input
                object.
                
                	The function then checks if the source and target pointers are
                equal, which indicates a no-op patch operation, before applying
                the necessary modifications to the input object. These modifications
                may involve removing an element from a list, adding a new element
                to a dictionary, or updating a field in an object. The `
                RemoveOperation` and `AddOperation` classes are used to perform
                these modifications, respectively removing or adding elements based
                on their corresponding keys. Finally, the modified input object
                is returned.

        Returns:
            instance of `JsonPatch: a modified version of the input `obj`.
            
            		- `obj`: The original object that was passed to the function as input.
            		- `subobj`: The subobject containing the value to be updated.
            		- `part`: The part of the subobject containing the value to be updated.
            		- `value`: The value being updated in the subobject.
            		- `from_ptr`: A pointer to the original object from which the value
            is being updated.
            		- `self.pointer`: The pointer used to determine if the source and
            target are equal, and to handle conflicts.
            		- `self.operation`: The operation containing the information about
            the update, including the `from` member.

        """
        try:
            if isinstance(self.operation['from'], self.pointer_cls):
                from_ptr = self.operation['from']
            else:
                from_ptr = self.pointer_cls(self.operation['from'])
        except KeyError as ex:
            raise InvalidJsonPatch(
                "The operation does not contain a 'from' member")

        subobj, part = from_ptr.to_last(obj)
        try:
            value = subobj[part]
        except (KeyError, IndexError) as ex:
            raise JsonPatchConflict(str(ex))

        # If source and target are equal, this is a no-op
        if self.pointer == from_ptr:
            return obj

        if isinstance(subobj, MutableMapping) and \
                self.pointer.contains(from_ptr):
            raise JsonPatchConflict('Cannot move values into their own children')

        obj = RemoveOperation({
            'op': 'remove',
            'path': self.operation['from']
        }, pointer_cls=self.pointer_cls).apply(obj)

        obj = AddOperation({
            'op': 'add',
            'path': self.location,
            'value': value
        }, pointer_cls=self.pointer_cls).apply(obj)

        return obj

    @property
    def from_path(self):
        """
        Returns the path portion of a URL, excluding the last segment, using the
        `pointer_cls` to get the from pointer and then joining the parts of the
        pointer into a path string.

        Returns:
            : a path string representing the component parts of a full path.
            
            		- `from_ptr`: A pointer to the `operation` dictionary containing
            information about the operation that resulted in the path being generated.
            		- `parts`: A list of strings representing the parts of the path,
            where each part is a directory or a file path separated by a '/'. The
            length of this list minus one indicates the number of components in
            the path.

        """
        from_ptr = self.pointer_cls(self.operation['from'])
        return '/'.join(from_ptr.parts[:-1])

    @property
    def from_key(self):
        """
        Retrieves the integer value associated with a given from key in a configuration
        dictionary, or returns the raw string value if it cannot be converted to
        an integer.

        Returns:
            int: an integer representing the final component of a pointer sequence
            or an exception raised if the input is not a valid pointer.

        """
        from_ptr = self.pointer_cls(self.operation['from'])
        try:
            return int(from_ptr.parts[-1])
        except TypeError:
            return from_ptr.parts[-1]

    @from_key.setter
    def from_key(self, value):
        """
        Sets the value of a part in an operation to a given string, updating the
        corresponding `from` pointer and storing the new value as the path of the
        updated `from` pointer in the operation's attribute map.

        Args:
            value (str): 5th element of the operation object `operation` and assigns
                it to the last part of the `from_ptr`, which is then stored as the
                value of `self.operation['from']`.

        """
        from_ptr = self.pointer_cls(self.operation['from'])
        from_ptr.parts[-1] = str(value)
        self.operation['from'] = from_ptr.path

    def _on_undo_remove(self, path, key):
        """
        Modifies a key value based on a comparison between a current key and a
        path key, with the goal of removing undo steps.

        Args:
            path (str): path of the node being undone, and is used to determine
                the new key value for the node after it has been removed.
            key (int): 16-bit value that is to be updated or removed within the
                undo stack.

        Returns:
            int: a new value for the `key` variable, determined by the relationships
            between the `path`, `from_path`, and `from_key` variables.

        """
        if self.from_path == path:
            if self.from_key >= key:
                self.from_key += 1
            else:
                key -= 1
        if self.path == path:
            if self.key > key:
                self.key += 1
            else:
                key += 1
        return key

    def _on_undo_add(self, path, key):
        """
        Updates the value of a `Key` instance when adding an item to an undo
        history. It decreases the `key` value if the added item has a lower `key`
        value than the current `from_key`, or increases the `key` value if the
        added item has a higher `key` value than the current `from_key`.

        Args:
            path (str): path of the undone action, which is used to determine
                whether the action can be retried or not.
            key (int): 2nd value in an undo pair and gets updated based on the
                comparison with the corresponding values from the `from_path` or
                `path` parameters.

        Returns:
            int: the new value of the `key` variable after applying the undo operation.

        """
        if self.from_path == path:
            if self.from_key > key:
                self.from_key -= 1
            else:
                key -= 1
        if self.path == path:
            if self.key > key:
                self.key -= 1
            else:
                key += 1
        return key


class TestOperation(PatchOperation):

    def apply(self, obj):
        """
        Takes an object and applies a JSON patch to it by following the pointers
        within the patch. If the resulting value does not match the expected value,
        a `JsonPatchTestFailed` exception is raised.

        Args:
            obj (`object`.): Python object to be operated on with the given JSON
                patch.
                
                		- `subobj`: This is the last element in the JSON object pointed
                to by the pointer `pointer`. Its type depends on the value of
                `part`, as explained next.
                		- `part`: This is an integer indicating the part of the JSON
                object that `subobj` belongs to. If `part` is None, then `subobj`
                is the entire JSON object. Otherwise, `subobj` represents a specific
                subtree of the JSON object.
                		- `value`: This is the value of the JSON object pointed to by
                `pointer`. It is used in the comparison step of the function to
                check if the result of the pointer walk is equal to the expected
                value.

        Returns:
            {0: a modified version of the input object with the specified operation
            applied.
            
            		- `obj`: The original JSON object being tested.
            		- `subobj`, `part`: A tuple containing the subobject and the part
            within the subobject that correspond to the value being checked. If
            the `val` variable is `None`, then `subobj` and `part` will be `(None,
            None)`.
            		- `value`: The expected value of the subobject or part within the
            subobject, as specified in the `operation` dictionary.
            
            	The `apply` function checks whether the value of the subobject or
            part within the subobject is equal to the expected value specified in
            the `operation` dictionary. If the values are not equal, a
            `JsonPatchTestFailed` exception is raised with a message containing
            the actual and expected values.

        """
        try:
            subobj, part = self.pointer.to_last(obj)
            if part is None:
                val = subobj
            else:
                val = self.pointer.walk(subobj, part)
        except JsonPointerException as ex:
            raise JsonPatchTestFailed(str(ex))

        try:
            value = self.operation['value']
        except KeyError as ex:
            raise InvalidJsonPatch(
                "The operation does not contain a 'value' member")

        if val != value:
            msg = '{0} ({1}) is not equal to tested value {2} ({3})'
            raise JsonPatchTestFailed(msg.format(val, type(val),
                                                 value, type(value)))

        return obj


class CopyOperation(PatchOperation):

    def apply(self, obj):
        """
        Performs a series of operations on an object, including creating a copy
        of the sub-object at a specific path, and then adding the sub-object to
        the original object using the `add` operation. The function takes an object
        as input and returns the modified object after applying the operations.

        Args:
            obj (Python object (instance or class) that supports method call.):
                2D array or object that will be modified by the apply() method.
                
                		- `from_ptr`: This is an instance of `PointerClass`, which
                contains the reference to the source object for the patch operation.
                		- `subobj`: This is a reference to a sub-object within the source
                object, obtained by calling `to_last(obj)` on the `from_ptr`.
                		- `part`: This is the part of the source object that contains
                the sub-object.
                		- `value`: This is the value of the sub-object that needs to be
                patched.
                		- `location`: This is a path string indicating where the patch
                operation should be applied within the object.
                
                	The function first tries to deep-copy the value of the sub-object
                using the `copy.deepcopy()` function. However, if this fails due
                to an IndexError or KeyError, a `JsonPatchConflict` exception is
                raised instead. The function then applies the patch operation to
                the `obj` by setting its `value` attribute to the result of the
                `apply` method call on the operation object, and returns the
                modified `obj`.

        Returns:
            obj: a modified version of the input `obj` with a new value added to
            a specific part of the object using the provided JSON patch.
            
            	1/ `op`: It represents the operation performed on the input object,
            specifically the 'add' operation in this case.
            	2/ `path`: It refers to the path or location in the input object where
            the operation was performed, which is the same as the function's
            `location` argument.
            	3/ `value`: It contains the value of the operation, which is a deep
            copy of the original value at the specified `part` in the input object.
            
            	Overall, the output of the `apply` function is an updated version of
            the input object with the requested operation applied to it.

        """
        try:
            from_ptr = self.pointer_cls(self.operation['from'])
        except KeyError as ex:
            raise InvalidJsonPatch(
                "The operation does not contain a 'from' member")

        subobj, part = from_ptr.to_last(obj)
        try:
            value = copy.deepcopy(subobj[part])
        except (KeyError, IndexError) as ex:
            raise JsonPatchConflict(str(ex))

        obj = AddOperation({
            'op': 'add',
            'path': self.location,
            'value': value
        }, pointer_cls=self.pointer_cls).apply(obj)

        return obj


class JsonPatch(object):
    json_dumper = staticmethod(json.dumps)
    json_loader = staticmethod(_jsonloads)

    operations = MappingProxyType({
        'remove': RemoveOperation,
        'add': AddOperation,
        'replace': ReplaceOperation,
        'move': MoveOperation,
        'test': TestOperation,
        'copy': CopyOperation,
    })

    def __init__(self, patch, pointer_cls=JsonPointer):
        """
        Of the `Patch` class verifies the structure of the patch document by
        retrieving each patch element and performing validation checks. If an
        invalid input is encountered, a `InvalidJsonPatch` exception is raised.

        Args:
            patch (str): JSON patch document that contains a sequence of operations
                to be applied to the original document, and it is verified for
                correct structure by retrieving each patch element and validating
                its type.
            pointer_cls (`type`.): Python class that defines the `JsonPointer`
                interface, which is used to store and manipulate the JSON patch document.
                
                		- `pointer_cls`: This is the class used to deserialize the pointer
                object. It may be provided as an argument to the function or it
                may be inferred from the input.
                		- `isinstance(op, basestring)`: This line of code checks if the
                value of the `op` field in the patch document is a string. If it
                is, an invalid JSON patch error is raised. The reason for this
                check is that the `patch` document is expected to be a sequence
                of operations, and each operation is represented as a string.
                		- `self._get_operation(op)`: This line of code calls the
                `_get_operation` method of the current instance, passing in the
                `op` field as an argument. This method is responsible for parsing
                the operation and validating its format.

        """
        self.patch = patch
        self.pointer_cls = pointer_cls

        # Verify that the structure of the patch document
        # is correct by retrieving each patch element.
        # Much of the validation is done in the initializer
        # though some is delayed until the patch is applied.
        for op in self.patch:
            # We're only checking for basestring in the following check
            # for two reasons:
            #
            # - It should come from JSON, which only allows strings as
            #   dictionary keys, so having a string here unambiguously means
            #   someone used: {"op": ..., ...} instead of [{"op": ..., ...}].
            #
            # - There's no possible false positive: if someone give a sequence
            #   of mappings, this won't raise.
            if isinstance(op, basestring):
                raise InvalidJsonPatch("Document is expected to be sequence of "
                                       "operations, got a sequence of strings.")

            self._get_operation(op)

    def __str__(self):
        return self.to_string()

    def __bool__(self):
        return bool(self.patch)

    __nonzero__ = __bool__

    def __iter__(self):
        return iter(self.patch)

    def __hash__(self):
        return hash(tuple(self._ops))

    def __eq__(self, other):
        """
        Compares two instances of `JsonPatch` by checking if their attribute `_ops`
        is equal. If the arguments are not instances of `JsonPatch`, the function
        returns `False`.

        Args:
            other (`JsonPatch`.): 2nd input for the comparison operator `__eq__()`
                and must be an instance of `JsonPatch`.
                
                		- `isinstance(other, JsonPatch)`: Checks if `other` is an instance
                of `JsonPatch`. If it's not, the method returns `False`.

        Returns:
            bool: a boolean indicating whether the two objects are equal based on
            their `_ops` attributes.

        """
        if not isinstance(other, JsonPatch):
            return False
        return self._ops == other._ops

    def __ne__(self, other):
        return not(self == other)

    @classmethod
    def from_string(cls, patch_str, loads=None, pointer_cls=JsonPointer):
        """
        Takes a JSON-formatted string as input and creates an instance of a Python
        class called `cls`. The `patch` attribute of the returned object refers
        to a nested object constructed from the input string using a loader function.

        Args:
            cls (Python class instance or a class name.): class that the function
                is defined in and serves as a proxy for that class when constructing
                instances of the class.
                
                		- `loads`: An optional argument that represents the `JsonLoader`
                instance to be used for loading the JSON data from the patch string.
                If not provided, the default loader defined in the `loads` attribute
                of the `cls` object will be used.
                		- `pointer_cls`: An optional argument that represents the class
                to use as a pointer for referencing the deserialized objects. If
                not provided, the default pointer class (`JsonPointer`) will be used.
            patch_str (str): JSON patch to be applied to the underlying JSON object,
                which is loaded from either `loads` or the `cls.json_loader`
                attribute using the `loads` parameter.
            loads (str): loading operation to perform on the JSON patch string,
                allowing for the creation of a `JsonPointer` object.
            pointer_cls (int): class that the pointer should be converted to.

        Returns:
            int: an instance of the given class with a `patch` attribute containing
            the deserialized JSON patch.

        """
        json_loader = loads or cls.json_loader
        patch = json_loader(patch_str)
        return cls(patch, pointer_cls=pointer_cls)

    @classmethod
    def from_diff(
            cls, src, dst, optimization=True, dumps=None,
            pointer_cls=JsonPointer,
    ):
        """
        Creates a DiffBuilder object and calls its `execute()` method to generate
        differences between two sources and produces an operation list. It returns
        a resulting object of the same class as the function's first argument,
        `cls`, with the `pointer_cls` parameter set to the specified value.

        Args:
            cls (Python callable (i.e., an object with a `__call__()` method).):
                class of the instance that will be returned after running the
                provided operations.
                
                		- `cls`: The input class to be deserialized from the given source
                and destination data.
                		- `src`: The source data for deserialization.
                		- `dst`: The destination data for deserialization.
                		- `optimization`: An optional parameter to enable or disable
                optimization of the deserialization process. If set to `True`, the
                function will use optimization techniques to reduce the amount of
                data transferred and processed.
                		- `dumps`: An optional parameter to specify a custom dump function
                to be used for serialization purposes. If not provided, the default
                JSON dump function of the class will be used.
                		- `pointer_cls`: An optional parameter to specify the pointer
                class to use when deserializing pointers. If not provided, the
                default pointer class of the class will be used.
            src (str): source code for which differences are to be calculated and
                compared with the `dst` parameter.
            dst (`object`.): 2nd half of the diff output that will be created by
                running the DiffBuilder object.
                
                		- `src`: The serialized input data.
                		- `dst`: The deserialized input data that is the target of the
                difference computation. If appropriate, this property may be
                destructured to expose its attributes or elements.
                		- `optimization`: A boolean value indicating whether optimization
                should be applied during the difference computation (True by default).
                		- `dumps`: An optional argument specifying the serializer used
                for dumping the data (None by default).
                		- `pointer_cls`: The class used to generate pointers for the
                deserialized data (optional, and default is `JsonPointer`).
            optimization (bool): difference between two data sources by
            dumps (str): JSON dumping function to use when comparing the source
                and destination objects.
            pointer_cls (int): class of the object that contains pointers to the
                data being diffed, which is used to customize the behavior of the
                `DiffBuilder` instance when performing the diff operation.

        Returns:
            instance of `Type: a `DiffOperation` object containing a list of
            operation objects representing the differences between the source and
            destination files.
            
            		- ops: This is a list of operations to be applied on the input data.
            Each operation in the list consists of an op_type and additional data
            required for that operation, such as pointer class.
            		- pointer_cls: This is the class used to store the pointers of the
            elements being operated on. It can be specified separately or inherited
            from the parent class.

        """
        json_dumper = dumps or cls.json_dumper
        builder = DiffBuilder(src, dst, json_dumper, pointer_cls=pointer_cls)
        builder._compare_values('', None, src, dst)
        ops = list(builder.execute())
        return cls(ops, pointer_cls=pointer_cls)

    def to_string(self, dumps=None):
        """
        Generates high-quality documentation for code based on the given information.
        It takes an optional parameter `dumps` and returns a JSON dumper that
        generates the documentation.

        Args:
            dumps (optional `json_dumper` or `self.json_dumper`.): optional JSON
                serializer to be used when converting the `patch` object into a string.
                
                		- `dumps`: If `None`, it means the default `json_dumper` is used.
                Otherwise, it refers to the specific `json_dumper` instance or
                class instance that should be used for serialization.

        Returns:
            str: a JSON-formatted string representation of the provided patch.

        """
        json_dumper = dumps or self.json_dumper
        return json_dumper(self.patch)

    @property
    def _ops(self):
        return tuple(map(self._get_operation, self.patch))

    def apply(self, obj, in_place=False):

        """
        Deep copies the input object, applies a series of operations to it, and
        returns the modified object.

        Args:
            obj (object, which is copy-deep copied when `in_place` is `False`.):
                ndarray or scalar object that undergoes operations through the
                function's private `_ops` attribute.
                
                		- If `in_place` is `False`, `obj` is copied before processing
                to ensure changes made to the copy are independent of the original.
            in_place (bool): whether the operations should be applied to the
                original object or copied before applying them, with a value of
                `True` (the default) to copy the object and a value of `False` to
                apply modifications directly to the original object.

        Returns:
            instance of the type to which the provided object is a/an instance of:
            a modified version of the input object, either the original or a deep
            copy, depending on the `in_place` parameter.
            
            	The output of the `apply` function is an instance of the class that
            `self` belongs to. This means that the output can be modified by
            accessing its attributes and methods directly, as well as by performing
            further operations on it.
            
            	If the `in_place` parameter was set to `True`, then a reference to
            the original `obj` instance will be retained within the new instance
            created in place of the input. This means that any modifications made
            to the new instance will also affect the original instance.
            
            	The returned output can have additional attributes or methods that
            are derived from the operations performed within the function body,
            which may provide more context or information related to the processing
            performed on `obj`.

        """
        if not in_place:
            obj = copy.deepcopy(obj)

        for operation in self._ops:
            obj = operation.apply(obj)

        return obj

    def _get_operation(self, operation):
        """
        Extracts operation information from a JSON patch and validates it before
        returning a class instance of a custom `operations` dictionary value.

        Args:
            operation (str): JSON patch operation that is to be performed on an
                object, and it is used to determine the appropriate class instance
                of the `Pointer` sub-class to use when applying the operation.

        Returns:
            Operation: an instance of a subclass of the `jsonpatch.operation`
            class, containing the operation and patch information.
            
            		- `operation`: This is the JSON patch operation that was passed to
            the function as input.
            		- `pointer_cls`: This is the class that the `operation` object belongs
            to. It is optional and can be a subclass of `jsonpatch.JsonPatch`.
            		- `cls`: This is the specific class instance that represents the
            operation, created by calling the corresponding factory method on the
            `operations` dict.

        """
        if 'op' not in operation:
            raise InvalidJsonPatch("Operation does not contain 'op' member")

        op = operation['op']

        if not isinstance(op, basestring):
            raise InvalidJsonPatch("Operation's op must be a string")

        if op not in self.operations:
            raise InvalidJsonPatch("Unknown operation {0!r}".format(op))

        cls = self.operations[op]
        return cls(operation, pointer_cls=self.pointer_cls)


class DiffBuilder(object):

    def __init__(self, src_doc, dst_doc, dumps=json.dumps, pointer_cls=JsonPointer):
        """
        Initializes an instance of a `JsonPointer` class, setting up index storage
        and pointer class fields, as well as populating the `src_doc` and `dst_doc`
        attributes with respective input documents.

        Args:
            src_doc (ndarray or any other serializable object.): original code
                documentation to be converted into the new documentation format.
                
                		- `src_doc`: A JSON-formatted object containing the source code
                documentation.
                		- `dst_doc`: A JSON-formatted object representing the target
                code documentation.
            dst_doc (list): target documentation to which the source code will be
                merged and generated.
            dumps (str): method used for serializing Python objects to strings,
                which is passed to the `json.dumps()` function for serialization.
            pointer_cls (int): class used to store and manage pointer information

        """
        self.dumps = dumps
        self.pointer_cls = pointer_cls
        self.index_storage = [{}, {}]
        self.index_storage2 = [[], []]
        self.__root = root = []
        self.src_doc = src_doc
        self.dst_doc = dst_doc
        root[:] = [root, root, None]

    def store_index(self, value, index, st):
        """
        Updates an index within a storage based on a value and its type, appending
        or adding the index to an existing list within the storage depending on
        if the key exists or not.

        Args:
            value (`(type_of_value, value)` typed key.): value that will be stored
                at the specified index within the storage.
                
                		- `value`: The serialized value to be stored in the index.
                		- `type(value)`: The type of the serialized value, which is used
                to determine the appropriate storage location in the `index_storage`
                or `index_storage2` dictionary.
            index (int): 2nd dimension of the key-value pair being stored in the
                storage, which is added to the list of values associated with the
                key in the storage.
            st (storage type.): storage object in which to store the indexed value.
                
                		- `st` is a dictionary-like object with key-value pairs.
                		- It has several methods and attributes, such as `.get()`,
                `.set()`, `.keys()`, `.values()`, and `.items()`.
                		- `st` is mutable, meaning it can be modified after initialization.
                		- The type of `st` is inferred based on the value passed to the
                function.
                		- If `st` is a string, then its type is inferred as a str.
                		- If `st` is a number or integer, then its type is inferred as
                an int.
                		- If `st` is a boolean, then its type is inferred as bool.
                		- If `st` is a tuple or list, then its type is inferred based
                on the types of its elements.

        """
        typed_key = (value, type(value))
        try:
            storage = self.index_storage[st]
            stored = storage.get(typed_key)
            if stored is None:
                storage[typed_key] = [index]
            else:
                storage[typed_key].append(index)

        except TypeError:
            self.index_storage2[st].append((typed_key, index))

    def take_index(self, value, st):
        """
        Retrieves a value from an index storage based on a typed key. It first
        checks the primary index storage, then falls back to the secondary index
        storage if the primary one fails.

        Args:
            value (`object`.): 2-tuple containing the key to look up in the index
                storage, which is then used to retrieve the associated value from
                the storage.
                
                		- `value`: The serialized value to be retrieved from the index.
                		- `st`: The storage type associated with the index, used to
                determine which storage container to use.
            st (storage slot index.): storage to check for the value being passed
                into the function.
                
                		- `st`: A stored value, which can be a tuple containing the key
                and its associated value or an empty tuple if the key is not found
                in the storage.
                		- `typed_key`: A typed tuple containing the value and its data
                type. This is created by passing the input value and its data type
                to the function.
                		- `self.index_storage`: An attribute storing the index of values
                associated with their corresponding keys, which can be accessed
                through a specific storage.
                		- `self.index_storage2`: Another attribute storing the index of
                values associated with their corresponding keys in a different storage.

        Returns:
            int: the value associated with the provided `value` and `stored` index,
            if found in the storage container.

        """
        typed_key = (value, type(value))
        try:
            stored = self.index_storage[st].get(typed_key)
            if stored:
                return stored.pop()

        except TypeError:
            storage = self.index_storage2[st]
            for i in range(len(storage)-1, -1, -1):
                if storage[i][0] == typed_key:
                    return storage.pop(i)[1]

    def insert(self, op):
        """
        Modifies a list by appending a new element to it and recursively updates
        the pointers of the elements in the list to reflect the new structure.

        Args:
            op (object reference.): 2-element list of the last element and the
                function itself, which are then concatenated to form the new root
                node of the binary tree.
                
                		- `op`: The input operation, which can be either an insertion
                or a mutation operation.

        Returns:
            list: a new tree node representing the original tree with an additional
            element added to the root position.

        """
        root = self.__root
        last = root[0]
        last[1] = root[0] = [last, root, op]
        return root[0]

    def remove(self, index):
        """
        Updates the linked list by removing the specified element and adjusting
        the links between adjacent elements to maintain the list's structure.

        Args:
            index (int): 3-element tuple containing the previous, current, and
                next links of a list element, which are updated accordingly by
                removing the specified element from the list.

        """
        link_prev, link_next, _ = index
        link_prev[1] = link_next
        link_next[0] = link_prev
        index[:] = []

    def iter_from(self, start):
        """
        Generates an iterator that yields subsequent nodes in a directed acyclic
        graph, starting from the specified `start` point.

        Args:
            start (tuple): 2-element tuple that contains the starting element of
                the iteration, with the first element being the root node and the
                second element being the current element to be yielded.

        """
        root = self.__root
        curr = start[1]
        while curr is not root:
            yield curr[2]
            curr = curr[1]

    def __iter__(self):
        """
        Generates a new iterable object that returns values from a specific part
        of an internal tree-like data structure by recursively traversing its root
        node and yields them in predefined manner until it reaches the topmost node.

        """
        root = self.__root
        curr = root[1]
        while curr is not root:
            yield curr[2]
            curr = curr[1]

    def execute(self):
        """
        Cycles through the nodes in a directed graph, applying operations to each
        node based on its type and the location of the operation.

        """
        root = self.__root
        curr = root[1]
        while curr is not root:
            if curr[1] is not root:
                op_first, op_second = curr[2], curr[1][2]
                if op_first.location == op_second.location and \
                        type(op_first) == RemoveOperation and \
                        type(op_second) == AddOperation:
                    yield ReplaceOperation({
                        'op': 'replace',
                        'path': op_second.location,
                        'value': op_second.operation['value'],
                    }, pointer_cls=self.pointer_cls).operation
                    curr = curr[1][1]
                    continue

            yield curr[2].operation
            curr = curr[1]

    def _item_added(self, path, key, item):
        """
        Handles the addition of an item to a store by updating the item's index,
        moving it to the correct location, and storing the new index for undo/redo
        purposes.

        Args:
            path (str): location where the item will be added or moved within the
                collection, and is used to determine the appropriate index for the
                operation.
            key (int): unique identifier of the item being added to the collection.
            item (object of type value.): item that is being added or removed from
                the container.
                
                		- `path`: A string representing the path of the item.
                		- `key`: An integer representing the unique key of the item
                within its path.
                		- `item`: The actual item data, which may have additional
                properties or attributes depending on its implementation class.

        """
        index = self.take_index(item, _ST_REMOVE)
        if index is not None:
            op = index[2]
            if type(op.key) == int and type(key) == int:
                for v in self.iter_from(index):
                    op.key = v._on_undo_remove(op.path, op.key)

            self.remove(index)
            if op.location != _path_join(path, key):
                new_op = MoveOperation({
                    'op': 'move',
                    'from': op.location,
                    'path': _path_join(path, key),
                }, pointer_cls=self.pointer_cls)
                self.insert(new_op)
        else:
            new_op = AddOperation({
                'op': 'add',
                'path': _path_join(path, key),
                'value': item,
            }, pointer_cls=self.pointer_cls)
            new_index = self.insert(new_op)
            self.store_index(item, new_index, _ST_ADD)

    def _item_removed(self, path, key, item):
        """
        Manages undo/redo operations for removing items from a dictionary. It
        creates a `PatchOperation` object representing the removal, updates the
        item's location in the operation stack if necessary, and removes the
        operation from the undo list if successful.

        Args:
            path (str): path of the item to be removed within the document.
            key (int): path to the item to be removed from the document.
            item (`object`.): 3rd item affected by the operation being handled by
                the function.
                
                		- `key`: The key of the item that is being removed.
                		- `item`: The actual item being removed, which may be a list or
                other type of data structure.
                		- `pointer_cls`: A class used to store pointers to items in the
                original document.

        """
        new_op = RemoveOperation({
            'op': 'remove',
            'path': _path_join(path, key),
        }, pointer_cls=self.pointer_cls)
        index = self.take_index(item, _ST_ADD)
        new_index = self.insert(new_op)
        if index is not None:
            op = index[2]
            # We can't rely on the op.key type since PatchOperation casts
            # the .key property to int and this path wrongly ends up being taken
            # for numeric string dict keys while the intention is to only handle lists.
            # So we do an explicit check on the item affected by the op instead.
            added_item = op.pointer.to_last(self.dst_doc)[0]
            if type(added_item) == list:
                for v in self.iter_from(index):
                    op.key = v._on_undo_add(op.path, op.key)

            self.remove(index)
            if new_op.location != op.location:
                new_op = MoveOperation({
                    'op': 'move',
                    'from': new_op.location,
                    'path': op.location,
                }, pointer_cls=self.pointer_cls)
                new_index[2] = new_op

            else:
                self.remove(new_index)

        else:
            self.store_index(item, new_index, _ST_REMOVE)

    def _item_replaced(self, path, key, item):
        """
        Replaces a value at a specified path within an object by executing a replace
        operation and updating the corresponding node with the provided item.

        Args:
            path (_______ (noun).): path of the node to replace in the tree.
                
                		- `path`: A string representing the path to the location where
                the item should be replaced.
                		+ It is the concatenation of several parts separated by underscores,
                where each part represents a nested path within the overall path.
                		+ Each part can be a substring of the previous part or a separate
                path altogether.
                		+ The total length of the path can be any positive integer, but
                it is limited to the maximum length that can be represented in a
                string.
            key (str): path of the item to be replaced in the hierarchy of paths
                provided in `path`.
            item (object/container, which is being replaced at the specified path
                by performing a `replace` operation.): data that will replace an
                existing item at the specified `path` within the object.
                
                		- `op`: The operation type, in this case, 'replace'.
                		- `path`: The path to the location where the item will be replaced,
                constructed by concatenating the path of the current location with
                the key.
                		- `value`: The item that needs to be replaced, which is either
                a scalar value or an object that can be serialized and deserialized.

        """
        self.insert(ReplaceOperation({
            'op': 'replace',
            'path': _path_join(path, key),
            'value': item,
        }, pointer_cls=self.pointer_cls))

    def _compare_dicts(self, path, src, dst):
        """
        Compares two dictionaries and performs actions based on differences in
        their keys and values. It identifies removed and added keys, calls respective
        removal and addition methods, and compares and synchronizes values for
        overlapping keys.

        Args:
            path (str): directory or file path where the comparison is taking place.
            src (dict): 1st dictionary to be compared against the `dst` parameter.
            dst (dict): 2nd dictionary to be compared with the `src` dictionary
                for differences and similarities.

        """
        src_keys = set(src.keys())
        dst_keys = set(dst.keys())
        added_keys = dst_keys - src_keys
        removed_keys = src_keys - dst_keys

        for key in removed_keys:
            self._item_removed(path, str(key), src[key])

        for key in added_keys:
            self._item_added(path, str(key), dst[key])

        for key in src_keys & dst_keys:
            self._compare_values(path, key, src[key], dst[key])

    def _compare_lists(self, path, src, dst):
        """
        Compares two lists and checks for any changes or differences between them.
        If there are any differences, it calls other functions to compare nested
        items such as dictionaries or sequences.

        Args:
            path (str): directory or file where the comparison is being performed.
            src (mutable mapping/sequence.): 1st list being compared to the second
                list.
                
                		- `len_src`: The length of the list `src`.
                		- `len_dst`: The length of the list `dst`.
                		- `max_len`: The maximum length of either `src` or `dst`.
                		- `min_len`: The minimum length of either `src` or `dst`.
                
                	The function then iterates through each element in `src` (or
                `dst`), checking if the corresponding element in `dst` exists. If
                it does, and if the objects are instances of `MutableMapping` or
                `MutableSequence`, then the function calls itself recursively to
                compare the two objects. Otherwise, it emits a removal event for
                the item in `src` and an addition event for the item in `dst`.
            dst (mutable sequence or mapping.): 2nd list to be compared with `src`.
                
                		- `len_src`: The length of the source list.
                		- `len_dst`: The length of the destination list.
                		- `max_len`: The maximum length of both lists.
                		- `min_len`: The minimum length of both lists.
                		- `old`: The value of an item in the source list at a given key.
                		- `new`: The value of an item in the destination list at the
                same key.
                		- `isinstance(old, MutableMapping)` and `isinstance(new,
                MutableMapping)`: Indicates that the old and new values are both
                mutable mapping types (i.e., dictionaries).
                		- `isinstance(old, MutableSequence)` and `isinstance(new,
                MutableSequence)`: Indicates that the old and new values are both
                mutable sequence types (i.e., lists or tuple).
                		- `self._compare_dicts`: A method called to compare two mutable
                mapping types.
                		- `self._item_removed`: A method called to remove an item from
                a list.
                		- `self._item_added`: A method called to add an item to a list.

        """
        len_src, len_dst = len(src), len(dst)
        max_len = max(len_src, len_dst)
        min_len = min(len_src, len_dst)
        for key in range(max_len):
            if key < min_len:
                old, new = src[key], dst[key]
                if old == new:
                    continue

                elif isinstance(old, MutableMapping) and \
                    isinstance(new, MutableMapping):
                    self._compare_dicts(_path_join(path, key), old, new)

                elif isinstance(old, MutableSequence) and \
                        isinstance(new, MutableSequence):
                    self._compare_lists(_path_join(path, key), old, new)

                else:
                    self._item_removed(path, key, old)
                    self._item_added(path, key, new)

            elif len_src > len_dst:
                self._item_removed(path, len_dst, src[key])

            else:
                self._item_added(path, key, dst[key])

    def _compare_values(self, path, key, src, dst):
        """
        Compares two values based on their type and JSON-like representation. If
        both values are mutable mapping or list, the function recursively calls
        itself to compare their elements. Otherwise, it checks if the JSON
        representations of the two values are equal, and if not, marks an item as
        replaced in the destination value.

        Args:
            path (str): full or relative path of the value being compared between
                `src` and `dst`.
            key (str): path to the specific value within the source and destination
                data that should be compared.
            src (`MutableMapping`.): existing value that should be compared to the
                corresponding value in the `dst` input parameter.
                
                		- `isinstance(src, MutableMapping)`: Checks if `src` is an
                instance of `MutableMapping`.
                		- `isinstance(dst, MutableMapping)`: Checks if `dst` is an
                instance of `MutableMapping`.
                		- `self._compare_dicts()`: Calls the `_compare_dicts` function
                with the argument `(path, key)` to compare the values in both `src`
                and `dst`.
                		- `isinstance(src, MutableSequence)`: Checks if `src` is an
                instance of `MutableSequence`.
                		- `isinstance(dst, MutableSequence)`: Checks if `dst` is an
                instance of `MutableSequence`.
                		- `self._compare_lists()`: Calls the `_compare_lists` function
                with the argument `(path, key)` to compare the values in both `src`
                and `dst`.
                		- `self.dumps()`: Returns the JSON representation of `src`.
                		- `self.dumps(dst)`: Returns the JSON representation of `dst`.
                		- `elif self.dumps(src) == self.dumps(dst)`: Checks if the JSON
                representation of `src` is equal to the JSON representation of
                `dst`. If they are equal, then `src` and `dst` have the same value,
                regardless of their types.
            dst (MutableMapping or MutableSequence.): 2nd element being compared
                with the `src` element.
                
                		- If `src` and `dst` are both instances of `MutableMapping`, the
                function calls `self._compare_dicts()` to compare the key-value
                pairs in the two objects.
                		- If `src` and `dst` are both instances of `MutableSequence`,
                the function calls `self._compare_lists()` to compare the sequences
                in the two objects.
                		- If the values of `src` and `dst` are already JSON-encoded using
                `json.dumps()`, and the encoded strings are identical, the function
                returns `True`.
                		- Otherwise, the function explanes that it will destructure `dst`
                if appropriate, or else provides a more detailed explanation of
                its properties.

        """
        if isinstance(src, MutableMapping) and \
                isinstance(dst, MutableMapping):
            self._compare_dicts(_path_join(path, key), src, dst)

        elif isinstance(src, MutableSequence) and \
                isinstance(dst, MutableSequence):
            self._compare_lists(_path_join(path, key), src, dst)

        # To ensure we catch changes to JSON, we can't rely on a simple
        # src == dst, because it would not recognize the difference between
        # 1 and True, among other things. Using json.dumps is the most
        # fool-proof way to ensure we catch type changes that matter to JSON
        # and ignore those that don't. The performance of this could be
        # improved by doing more direct type checks, but we'd need to be
        # careful to accept type changes that don't matter when JSONified.
        elif self.dumps(src) == self.dumps(dst):
            return

        else:
            self._item_replaced(path, key, dst)


def _path_join(path, key):
    """
    Combines two paths by concatenating them with an additional separator character,
    taking into account special characters and representing null as an empty path.

    Args:
        path (str): base path for joining key values.
        key (str): 0-based index or name of a directory or file within the `path`,
            which is then converted to a pathname string by adding a leading `/`
            and any necessary special characters (e.g., `'~'` for the home directory).

    Returns:
        str: a concatenation of the input `path` and a key value, separated by a
        forward slash.

    """
    if key is None:
        return path

    return path + '/' + str(key).replace('~', '~0').replace('/', '~1')
